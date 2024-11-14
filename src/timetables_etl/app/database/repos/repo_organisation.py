import logging

from ..client import BodsDB
from ..models import OrganisationDataset, OrganisationDatasetrevision
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
        return self._fetch_one(statement)

    @handle_repository_errors
    def get_by_dataset_id(self, dataset_id: int) -> list[OrganisationDatasetrevision]:
        """
        Get all revisions for a dataset
        """
        statement = self._build_query().where(self._model.dataset_id == dataset_id)
        return self._fetch_all(statement)
