"""
Caching for File Attributes
"""

from enum import Enum

from common_layer.database.client import SqlDB
from common_layer.database.models import OrganisationDatasetRevision
from common_layer.database.repos import (
    OrganisationDatasetRepo,
    OrganisationTXCFileAttributesRepo,
    TransmodelStopActivityRepo,
)
from common_layer.dynamodb.client.cache import DynamoDBCache
from common_layer.dynamodb.models import TXCFileAttributes
from common_layer.dynamodb.utils import dataclass_to_dict
from common_layer.exceptions.pipeline_exceptions import PipelineException
from structlog.stdlib import get_logger


class CachedDataType(str, Enum):
    """
    Types of Cached Data
    """

    LIVE_TXC_FILE_ATTRIBUTES = "live_txc_file_attributes"
    STOP_ACTIVITY_ID_MAP = "transmodel_stop_activity_id_map"


log = get_logger()


class FileProcessingDataManager:
    """
    Manage shared data required for file-level processing
    Handles pre-fetching, caching, and retrieval of different data types.
    """

    def __init__(self, db: SqlDB, dynamodb: DynamoDBCache):
        """
        Initialize the data manager with database and DynamoDB clients.
        """
        self._db = db
        self._dynamodb = dynamodb

    def prefetch_and_cache_data(self, revision: OrganisationDatasetRevision) -> None:
        """
        Pre-fetch and cache data required for file-level processing.
        """
        self._cache_live_txc_file_attributes(revision)
        self.get_or_compute_stop_activity_id_map()

    def _cache_live_txc_file_attributes(
        self, revision: OrganisationDatasetRevision
    ) -> None:
        """
        Fetch and cache live TXCFileAttributes data for the given revision.
        """
        dataset_repo = OrganisationDatasetRepo(self._db)
        dataset = dataset_repo.get_by_id(revision.dataset_id)
        if dataset is None:
            raise PipelineException(
                f"Dataset id {revision.dataset_id} belonging to revision id {revision.id} not found"
            )

        live_revision_id = dataset.live_revision_id
        if not live_revision_id:
            log.info(
                "No live revision for Dataset; no TXCFileAttributes to cache",
                dataset_id=dataset.id,
            )
            return

        txc_file_attributes_repo = OrganisationTXCFileAttributesRepo(self._db)
        live_attributes = txc_file_attributes_repo.get_by_revision_id(live_revision_id)
        live_attributes_to_cache = [
            dataclass_to_dict(TXCFileAttributes.from_orm(att))
            for att in live_attributes
        ]
        log.info("Caching TXCFileAttributes", count=len(live_attributes_to_cache))

        cache_key = self._generate_cache_key(
            CachedDataType.LIVE_TXC_FILE_ATTRIBUTES,
            prefix=f"revision-{revision.id}",
        )
        self._dynamodb.put(cache_key, live_attributes_to_cache, ttl=3600)

    def get_cached_live_txc_file_attributes(
        self, revision_id: int
    ) -> list[TXCFileAttributes] | None:
        """
        Get the Cached Attributes from DynamoDB
        """
        cache_key = self._generate_cache_key(
            CachedDataType.LIVE_TXC_FILE_ATTRIBUTES, prefix=f"revision-{revision_id}"
        )

        cached_attributes = self._dynamodb.get(cache_key)
        if not cached_attributes:
            return None

        return [
            TXCFileAttributes.from_dict(cached_attribute)  # type: ignore
            for cached_attribute in cached_attributes
        ]

    def get_or_compute_stop_activity_id_map(self) -> dict[str, int]:
        """
        Get stop activity id map from the DynamoDB cache
        or compute and cache it if not found
        """
        cache_key = self._generate_cache_key(CachedDataType.STOP_ACTIVITY_ID_MAP)
        return self._dynamodb.get_or_compute(
            cache_key,
            compute_fn=lambda: TransmodelStopActivityRepo(
                self._db
            ).get_activity_id_map(),
            ttl=3600,
        )

    @staticmethod
    def _generate_cache_key(
        data_type: CachedDataType,
        prefix: str | None = None,
    ) -> str:
        """
        Generate a cache key for the given data_type with an optional prefix
        """
        if prefix:
            return f"{prefix}-{data_type.value}"
        return data_type.value
