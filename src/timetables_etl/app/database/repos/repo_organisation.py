"""
SQLAlchemy Organisation Repos
"""

import logging

from ..client import BodsDB
from ..models import (
    OrganisationDataset,
    OrganisationDatasetrevision,
    OrganisationOrganisation,
    OrganisationTXCFileAttributes,
)
from .exceptions import RevisionNotFoundException
from .repo_common import BaseRepository, handle_repository_errors

logger = logging.getLogger(__name__)


class OrganisationDatasetRepo(BaseRepository[OrganisationDataset]):
    """
    Repository for managing OrganisationDataset entities
    Table: organisation_dataset
    """

    def __init__(self, db: BodsDB):
        super().__init__(db, OrganisationDataset)

    @handle_repository_errors
    def get_by_id(self, dataset_id: int) -> OrganisationDataset | None:
        """
        Get OrganisationDataset by ID
        """
        statement = self._build_query().where(self._model.id == dataset_id)
        return self._fetch_one(statement)


class OrganisationDatasetRevisionRepo(BaseRepository[OrganisationDatasetrevision]):
    """
    Repository for managing OrganisationDatasetrevision entities
    Table: organisation_datasetrevision
    """

    def __init__(self, db: BodsDB):
        super().__init__(db, OrganisationDatasetrevision)

    @handle_repository_errors
    def get_by_id(self, revision_id: int) -> OrganisationDatasetrevision | None:
        """
        Get OrganisationDatasetrevision by ID
        """
        statement = self._build_query().where(self._model.id == revision_id)
        revision = self._fetch_one(statement)
        if revision is None:
            raise RevisionNotFoundException()
        return revision

    @handle_repository_errors
    def get_by_dataset_id(self, dataset_id: int) -> list[OrganisationDatasetrevision]:
        """
        Get all revisions for a dataset
        """
        statement = self._build_query().where(self._model.dataset_id == dataset_id)
        return self._fetch_all(statement)


class OrganisationTXCFileAttributesRepo(BaseRepository[OrganisationTXCFileAttributes]):
    """Repository for managing TXC File Attributes entities"""

    def __init__(self, db: BodsDB):
        super().__init__(db, OrganisationTXCFileAttributes)

    @handle_repository_errors
    def get_by_id(self, attributes_id: int) -> OrganisationTXCFileAttributes | None:
        """Get by ID"""
        statement = self._build_query().where(self._model.id == attributes_id)
        return self._fetch_one(statement)


class OrganisationOrganisationRepo(BaseRepository[OrganisationOrganisation]):
    """Repository for managing Organisation entities"""

    def __init__(self, db: BodsDB):
        super().__init__(db, OrganisationOrganisation)

    @handle_repository_errors
    def get_by_id(self, org_id: int) -> OrganisationOrganisation | None:
        """Get by ID"""
        statement = self._build_query().where(self._model.id == org_id)
        return self._fetch_one(statement)
