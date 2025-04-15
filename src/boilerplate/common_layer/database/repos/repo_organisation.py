"""
SQLAlchemy Organisation Repos
"""

from datetime import UTC, datetime

from common_layer.enums import FeedStatus
from sqlalchemy import and_, func, select
from structlog.stdlib import get_logger

from ..client import SqlDB
from ..dataclasses import RevisionStats, TXCFileStats
from ..exceptions import (
    OrganisationDatasetNotFound,
    OrganisationDatasetRevisionNotFound,
    OrganisationTXCFileAttributesNotFound,
)
from ..models import (
    OrganisationDataset,
    OrganisationDatasetMetadata,
    OrganisationDatasetRevision,
    OrganisationOrganisation,
    OrganisationTXCFileAttributes,
)
from .operation_decorator import handle_repository_errors
from .repo_common import BaseRepositoryWithId
from .utils import date_to_datetime

log = get_logger()


class OrganisationDatasetRepo(BaseRepositoryWithId[OrganisationDataset]):
    """
    Repository for managing OrganisationDataset entities
    Table: organisation_dataset
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, OrganisationDataset)

    @handle_repository_errors
    def require_by_id(self, dataset_id: int) -> OrganisationDataset:
        """
        Return a Dataset Revision otherwise raise OrganisationDatasetNotFound exception
        """
        revision = self.get_by_id(dataset_id)
        if revision is None:
            raise OrganisationDatasetNotFound(dataset_id=dataset_id)
        return revision

    @handle_repository_errors
    def get_published_datasets(
        self, live_revision_ids: list[int]
    ) -> list[OrganisationDataset]:
        """
        Get all published datasets
        """
        statement = self._build_query().where(
            self._model.live_revision_id.in_(live_revision_ids)
        )
        return self._fetch_all(statement)

    @handle_repository_errors
    def update_live_revision(self, dataset_id: int, new_live_revision_id: int) -> None:
        """
        Update live revision id
        """
        statement = self._build_query().where(self._model.id == dataset_id)

        def update_live_revision(record: OrganisationDataset) -> None:
            record.live_revision_id = new_live_revision_id

        self._execute_update(update_live_revision, statement)


class OrganisationDatasetMetdataRepo(BaseRepositoryWithId[OrganisationDatasetMetadata]):
    """
    Repository for managing OrganisationDatasetMetadata entities
    Table: organisation_datasetmetadata
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, OrganisationDatasetMetadata)

    @handle_repository_errors
    def get_by_revision_id(
        self, revision_id: int
    ) -> OrganisationDatasetMetadata | None:
        """
        Get all metadata for a revision id
        """
        statement = self._build_query().where(self._model.revision_id == revision_id)
        return self._fetch_one(statement)


class OrganisationDatasetRevisionRepo(
    BaseRepositoryWithId[OrganisationDatasetRevision]
):
    """
    Repository for managing OrganisationDatasetrevision entities
    Table: organisation_datasetrevision
    """

    def __init__(self, db: SqlDB) -> None:
        super().__init__(db, OrganisationDatasetRevision)

    @handle_repository_errors
    def require_by_id(self, dataset_id: int) -> OrganisationDatasetRevision:
        """
        Return a Dataset Revision otherwise raise OrganisationDatasetRevisionNotFound exception
        """
        revision = self.get_by_id(dataset_id)
        if revision is None:
            raise OrganisationDatasetRevisionNotFound(f"ID {dataset_id} not found")
        return revision

    @handle_repository_errors
    def get_by_dataset_id(self, dataset_id: int) -> list[OrganisationDatasetRevision]:
        """
        Get all revisions for a dataset
        """
        statement = self._build_query().where(self._model.dataset_id == dataset_id)
        return self._fetch_all(statement)

    @handle_repository_errors
    def update_original_file_hash(self, revision_id: int, new_hash: str) -> None:
        """
        Update the original file hash for a specific revision
        """
        statement = self._build_query().where(self._model.id == revision_id)

        def update_hash(record: OrganisationDatasetRevision) -> None:
            record.original_file_hash = new_hash

        self._execute_update(update_hash, statement)

    @handle_repository_errors
    def update_modified_file_hash(self, revision_id: int, new_hash: str) -> None:
        """
        Update the modified file hash for a specific revision
        """
        statement = self._build_query().where(self._model.id == revision_id)

        def update_hash(record: OrganisationDatasetRevision) -> None:
            record.modified_file_hash = new_hash

        self._execute_update(update_hash, statement)

    @handle_repository_errors
    def get_live_revisions(
        self, revision_id_list: list[int]
    ) -> list[OrganisationDatasetRevision]:
        """
        Get Revisions that are live and published
        """
        statement = self._build_query().where(
            and_(
                self._model.id.in_(revision_id_list),
                self._model.status == FeedStatus.LIVE,
                self._model.is_published.is_(True),
            )
        )
        return self._fetch_all(statement)

    @handle_repository_errors
    def publish_revision(self, revision_id: int) -> None:
        """
        Publish a revision by the given revision_id.

        This will:
            - Update the FeedStatus from Success => Live
            - Set is_published and published_at fields
        """
        statement = self._build_query().where(self._model.id == revision_id)
        now = datetime.now(UTC)

        def update_record(record: OrganisationDatasetRevision) -> None:
            if record.is_published:
                return None
            if record.status == FeedStatus.SUCCESS:
                log.info("Publishing revision", revision_id=record.id)
                record.status = FeedStatus.LIVE
                record.is_published = True
                record.published_at = now
            else:
                log.warning(
                    "Could not publish revision because status is not success",
                    revision_status=record.status,
                )
            return None

        self._execute_update(update_record, statement)

    @handle_repository_errors
    def update_stats(self, revision_id: int, revision_stats: RevisionStats) -> None:
        """
        Update fields on a dataset revision using the values from RevisionStats.
        """
        statement = self._build_query().where(self._model.id == revision_id)

        def update_record(record: OrganisationDatasetRevision) -> None:
            log.info("Updating metadata fields for revision", revision_id=record.id)

            record.publisher_creation_datetime = (
                revision_stats.publisher_creation_datetime
            )
            record.publisher_modified_datetime = (
                revision_stats.publisher_modification_datetime
            )
            record.first_expiring_service = date_to_datetime(
                revision_stats.first_expiring_service
            )
            record.last_expiring_service = date_to_datetime(
                revision_stats.last_expiring_service
            )
            record.first_service_start = date_to_datetime(
                revision_stats.first_service_start
            )

        self._execute_update(update_record, statement)


class OrganisationTXCFileAttributesRepo(
    BaseRepositoryWithId[OrganisationTXCFileAttributes]
):
    """Repository for managing TXC File Attributes entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, OrganisationTXCFileAttributes)

    @handle_repository_errors
    def require_by_id(self, attrs_id: int) -> OrganisationTXCFileAttributes:
        """
        Return a Organisation File Attributes by ID else raise Exception
        """
        attrs = self.get_by_id(attrs_id)
        if attrs is None:
            raise OrganisationTXCFileAttributesNotFound(f"ID {attrs_id} not found")
        return attrs

    @handle_repository_errors
    def get_by_revision_id(
        self, revision_id: int
    ) -> list[OrganisationTXCFileAttributes]:
        """
        Get TXC File Attributes by OrganisationDatasetRevision ID
        """
        statement = self._build_query().where(self._model.revision_id == revision_id)
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_revision_id_and_filename(
        self, revision_id: int, filename: str
    ) -> OrganisationTXCFileAttributes | None:
        """
        Get all TXCFileAttributes by given revision ID
        """
        statement = self._build_query().where(
            self._model.revision_id == revision_id and self._model.filename == filename
        )
        return self._fetch_one(statement)

    @handle_repository_errors
    def get_by_service_code(
        self, service_codes: list[str]
    ) -> list[OrganisationTXCFileAttributes]:
        """
        Get TXC File Attributes by service code
        """
        statement = self._build_query().where(
            self._model.service_code.in_(service_codes)
        )
        return self._fetch_all(statement)

    def get_file_datetime_stats_by_revision_id(self, revision_id: int) -> TXCFileStats:
        """
        Return the earliest creation_datetime and latest modification_datetime
        across all TXC files for a given dataset revision.
        """
        stmt = select(
            func.min(self._model.creation_datetime),
            func.max(self._model.modification_datetime),
        ).where(self._model.revision_id == revision_id)

        with self._db.session_scope() as session:
            result = session.execute(stmt).one_or_none()
            if result is None:
                return TXCFileStats(None, None)
            return TXCFileStats(
                first_creation_datetime=result[0], last_modification_datetime=result[1]
            )


class OrganisationOrganisationRepo(BaseRepositoryWithId[OrganisationOrganisation]):
    """Repository for managing Organisation entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, OrganisationOrganisation)
