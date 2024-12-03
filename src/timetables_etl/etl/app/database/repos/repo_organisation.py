"""
SQLAlchemy Organisation Repos
"""

import logging

from ..client import BodsDB
from ..models import (
    OrganisationDataset,
    OrganisationDatasetRevision,
    OrganisationOrganisation,
    OrganisationTXCFileAttributes,
)
from . import exceptions
from .repo_common import BaseRepository, BaseRepositoryWithId, handle_repository_errors

logger = logging.getLogger(__name__)


class OrganisationDatasetRepo(BaseRepositoryWithId[OrganisationDataset]):
    """
    Repository for managing OrganisationDataset entities
    Table: organisation_dataset
    """

    def __init__(self, db: BodsDB):
        super().__init__(db, OrganisationDataset)


class OrganisationDatasetRevisionRepo(BaseRepository[OrganisationDatasetRevision]):
    """
    Repository for managing OrganisationDatasetrevision entities
    Table: organisation_datasetrevision
    """

    def __init__(self, db: BodsDB):
        super().__init__(db, OrganisationDatasetRevision)

    @handle_repository_errors
    def get_by_id(self, revision_id: int) -> OrganisationDatasetRevision:
        """
        Get OrganisationDatasetrevision by ID
        """
        statement = self._build_query().where(self._model.id == revision_id)
        revision = self._fetch_one(statement)
        if revision is None:
            raise exceptions.RevisionNotFoundException()
        return revision

    @handle_repository_errors
    def get_by_dataset_id(self, dataset_id: int) -> list[OrganisationDatasetRevision]:
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
    def get_by_id(self, attributes_id: int) -> OrganisationTXCFileAttributes:
        """Get by ID"""
        statement = self._build_query().where(self._model.id == attributes_id)
        file = self._fetch_one(statement)
        if file is None:
            raise exceptions.FileAttributesNotFoundException()
        return file


class OrganisationOrganisationRepo(BaseRepositoryWithId[OrganisationOrganisation]):
    """Repository for managing Organisation entities"""

    def __init__(self, db: BodsDB):
        super().__init__(db, OrganisationOrganisation)
