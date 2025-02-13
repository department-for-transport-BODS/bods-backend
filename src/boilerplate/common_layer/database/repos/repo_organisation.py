"""
SQLAlchemy Organisation Repos
"""

from datetime import UTC, datetime

from common_layer.enums import FeedStatus
from sqlalchemy import and_
from structlog.stdlib import get_logger

from ..client import SqlDB
from ..models import (
    OrganisationDataset,
    OrganisationDatasetRevision,
    OrganisationOrganisation,
    OrganisationTXCFileAttributes,
)
from .operation_decorator import handle_repository_errors
from .repo_common import BaseRepositoryWithId

log = get_logger()


class OrganisationDatasetRepo(BaseRepositoryWithId[OrganisationDataset]):
    """
    Repository for managing OrganisationDataset entities
    Table: organisation_dataset
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, OrganisationDataset)

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


class OrganisationDatasetRevisionRepo(
    BaseRepositoryWithId[OrganisationDatasetRevision]
):
    """
    Repository for managing OrganisationDatasetrevision entities
    Table: organisation_datasetrevision
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, OrganisationDatasetRevision)

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


class OrganisationTXCFileAttributesRepo(
    BaseRepositoryWithId[OrganisationTXCFileAttributes]
):
    """Repository for managing TXC File Attributes entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, OrganisationTXCFileAttributes)

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


class OrganisationOrganisationRepo(BaseRepositoryWithId[OrganisationOrganisation]):
    """Repository for managing Organisation entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, OrganisationOrganisation)
