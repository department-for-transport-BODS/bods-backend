"""
Database Calls
"""

import logging
from datetime import UTC, datetime

from ..client import SqlDB
from ..models.model_pipelines import DatasetETLTaskResult, ETLErrorCode, TaskState
from .operation_decorator import handle_repository_errors
from .repo_common import BaseRepository

logger = logging.getLogger(__name__)


class ETLTaskResultRepo(BaseRepository[DatasetETLTaskResult]):
    """
    Repository for managing ETLTaskResult entities
    Table: pipelines_datasetetltaskresult
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, DatasetETLTaskResult)

    @handle_repository_errors
    def get_by_id(self, task_id: int) -> DatasetETLTaskResult | None:
        """
        Get ETL Task by ID
        """
        statement = self._build_query().where(self._model.id == task_id)
        task = self._fetch_one(statement)
        return task

    @handle_repository_errors
    def mark_success(self, task_id: int) -> None:
        """
        Mark task as successful and clear error fields
        """

        def update_func(task: DatasetETLTaskResult) -> None:
            task.status = TaskState.SUCCESS
            task.completed = datetime.now(UTC)
            task.task_name_failed = ""
            task.error_code = None

        statement = self._build_query().where(self._model.id == task_id)
        self._update_one(statement, update_func)

    @handle_repository_errors
    def mark_error(
        self, task_id: int, task_name: str, error_code: ETLErrorCode
    ) -> None:
        """
        Mark task as failed with specific error information
        """

        def update_func(task: DatasetETLTaskResult) -> None:
            if task.status != TaskState.FAILURE:
                task.status = TaskState.FAILURE
                task.completed = datetime.now(UTC)
                task.task_name_failed = task_name
                task.error_code = error_code

        statement = self._build_query().where(self._model.id == task_id)
        self._update_one(statement, update_func)

    @handle_repository_errors
    def update_progress(self, task_id: int, progress: int) -> None:
        """
        Update the progress of an ETL task
        """

        def update_func(task: DatasetETLTaskResult) -> None:
            task.progress = progress

        statement = self._build_query().where(self._model.id == task_id)
        self._update_one(statement, update_func)
