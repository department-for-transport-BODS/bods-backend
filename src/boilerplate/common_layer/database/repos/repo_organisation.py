"""
SQLAlchemy Organisation Repos
"""

from common_layer.db.models import OrganisationTxcfileattributes

from ..client import SqlDB
from ..models import (
    OrganisationDataset,
    OrganisationDatasetRevision,
    OrganisationOrganisation,
    OrganisationTXCFileAttributes,
)
from .operation_decorator import handle_repository_errors
from .repo_common import BaseRepositoryWithId


class OrganisationDatasetRepo(BaseRepositoryWithId[OrganisationDataset]):
    """
    Repository for managing OrganisationDataset entities
    Table: organisation_dataset
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, OrganisationDataset)


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


class OrganisationOrganisationRepo(BaseRepositoryWithId[OrganisationOrganisation]):
    """Repository for managing Organisation entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, OrganisationOrganisation)
