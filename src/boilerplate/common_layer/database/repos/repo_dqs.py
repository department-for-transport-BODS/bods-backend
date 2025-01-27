"""
SQLAlchemy DQS Repos
"""

from ..client import SqlDB
from ..models.model_dqs import (DQSChecks, DQSObservationResults, DQSReport,
                                DQSTaskResults, DQSTaskState)
from .operation_decorator import handle_repository_errors
from .repo_common import BaseRepositoryWithId


class DQSReportRepo(BaseRepositoryWithId[DQSReport]):
    """
    Repository for managing OrganisationDataset entities
    Table: organisation_dataset
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, DQSReport)
    
    @handle_repository_errors
    def get_by_revision_id(self, revision_id: int) -> list[DQSReport]:
        """
        Get report for a revision
        """
        statement = self._build_query().where(self._model.revision_id == revision_id).first()
        return self._fetch_one(statement)

    @handle_repository_errors
    def delete_report_by_revision_id(self, revision_id: int) -> bool:
        """
        Get report for a revision
        """
        statement = self._build_query().where(self._model.revision_id == revision_id).first()
        return self._delete_and_commit(statement)
    
    @handle_repository_errors
    def create_report_for_revision(self, revision: object) -> bool:
        """
        Create a report object for a revision_id
        """
        new_report = DQSReport(file_name="", status=DQSTaskState.PENDING.value, revision=revision)
        return self.insert(new_report)

class DQSChecksRepo(
    BaseRepositoryWithId[DQSChecks]
):
    """
    Repository for managing OrganisationDatasetrevision entities
    Table: organisation_datasetrevision
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, DQSChecks)

    @handle_repository_errors
    def get_all_checks(self) -> list[DQSChecks]:
        """
        Get all DQS checks
        """
        statement = self._build_query()
        return self._fetch_all(statement)


class DQSTaskResultsRepo(
    BaseRepositoryWithId[DQSTaskResults]
):
    """Repository for managing TXC File Attributes entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, DQSTaskResults)

    @handle_repository_errors
    def get_by_revision_id(
        self, revision_id: int
    ) -> list[DQSTaskResults]:
        statement = self._build_query().where(self._model.revision_id == revision_id)
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_revision_id_and_filename(
        self, revision_id: int, filename: str
    ) -> DQSTaskResults | None:
        """
        Get all TXCFileAttributes by given revision ID
        """
        statement = self._build_query().where(
            self._model.revision_id == revision_id and self._model.filename == filename
        )
        return self._fetch_one(statement)


class DQSObservationResultsRepo(BaseRepositoryWithId[DQSObservationResults]):
    """Repository for managing Organisation entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, DQSObservationResults)
