"""
Database Calls
"""

from datetime import UTC, datetime

from ..client import SqlDB
from ..exceptions import PipelinesDatasetETLTaskResultNotFound
from ..models import (
    DatasetETLTaskResult,
    ETLErrorCode,
    FileProcessingResult,
    PipelineErrorCode,
    PipelineProcessingStep,
    TaskState,
)
from .operation_decorator import handle_repository_errors
from .repo_common import BaseRepositoryWithId


class ETLTaskResultRepo(BaseRepositoryWithId[DatasetETLTaskResult]):
    """
    Repository for managing ETLTaskResult entities
    Table: pipelines_datasetetltaskresult
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, DatasetETLTaskResult)

    @handle_repository_errors
    def require_by_id(self, task_id: int) -> DatasetETLTaskResult:
        """
        Get ETL Task by ID
        """
        result = self.get_by_id(task_id)
        if result is None:
            raise PipelinesDatasetETLTaskResultNotFound(f"ID {task_id} not found")
        return result

    @handle_repository_errors
    def get_by_revision_id(self, revision_id: int) -> list[DatasetETLTaskResult] | None:
        """
        Retrieve all DatasetETLTaskResult for a specific revision
        """
        statement = self._build_query().where(self._model.revision_id == revision_id)
        return self._fetch_all(statement)

    @handle_repository_errors
    def mark_success(self, task_id: int) -> None:
        """
        Mark task as successful and clear error fields
        """

        def update_func(task: DatasetETLTaskResult) -> None:
            task.status = TaskState.SUCCESS
            task.completed = datetime.now(UTC)
            task.task_name_failed = ""
            task.error_code = ETLErrorCode.EMPTY

        statement = self._build_query().where(self._model.id == task_id)
        self._update_one(statement, update_func)

    @handle_repository_errors
    def mark_error(
        self,
        task_id: int,
        task_name: str,
        error_code: ETLErrorCode,
        additional_info: str,
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
                task.additional_info = additional_info

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


class FileProcessingResultRepo(BaseRepositoryWithId[FileProcessingResult]):
    """
    Repository for FileProcessingResult model with specific query methods
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, FileProcessingResult)

    def get_by_task_id(self, task_id: str) -> FileProcessingResult | None:
        """
        Retrieve a FileProcessingResult by its task_id
        """
        statement = self._build_query().where(self._model.task_id == task_id)
        return self._fetch_one(statement)

    def get_by_revision_id(self, revision_id: int) -> list[FileProcessingResult]:
        """
        Retrieve all FileProcessingResults for a specific revision

        """
        statement = self._build_query().where(self._model.revision_id == revision_id)
        return self._fetch_all(statement)

    def get_by_processing_step_id(
        self, processing_step_id: int
    ) -> list[FileProcessingResult]:
        """
        Retrieve all FileProcessingResults for a specific processing step

        """
        statement = self._build_query().where(
            self._model.pipeline_processing_step_id == processing_step_id
        )
        return self._fetch_all(statement)


class PipelineErrorCodeRepository(BaseRepositoryWithId[PipelineErrorCode]):
    """
    Repository for PipelineErrorCode model with specific query methods
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, PipelineErrorCode)

    def get_by_error(self, error: str) -> PipelineErrorCode | None:
        """
        Retrieve a PipelineErrorCode by its error string

        """
        statement = self._build_query().where(self._model.error == error)
        return self._fetch_one(statement)

    def get_or_create_by_error_code(self, status: ETLErrorCode) -> PipelineErrorCode:
        """
        Retrieves the pipeline error code object for a given task state.
        Creates a new pipeline error if it doesn't exist.
        """
        existing_error = self.get_by_error(status.value)
        if existing_error:
            return existing_error

        # Create new error if not found
        new_error = PipelineErrorCode(error=status.value)
        return self.insert(new_error)


class PipelineProcessingStepRepository(BaseRepositoryWithId[PipelineProcessingStep]):
    """
    Repository for PipelineProcessingStep model with specific query methods
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, PipelineProcessingStep)

    def get_by_name(self, name: str) -> list[PipelineProcessingStep]:
        """
        Retrieve a PipelineProcessingStep by its name
        """
        statement = self._build_query().where(self._model.name == name)
        return self._fetch_all(statement)

    def get_by_category(self, category: str) -> list[PipelineProcessingStep]:
        """
        Retrieve all PipelineProcessingSteps for a specific category
        """
        statement = self._build_query().where(self._model.category == category)
        return self._fetch_all(statement)

    def get_by_name_and_category(
        self, name: str, category: str
    ) -> PipelineProcessingStep | None:
        """
        Retrieve a unique PipelineProcessingStep by its name and category
        """
        statement = self._build_query().where(
            self._model.name == name, self._model.category == category
        )
        return self._fetch_one(statement)

    def get_or_create_by_name_and_category(
        self, name: str, category: str
    ) -> PipelineProcessingStep:
        """
        Retrieves the processing step by name and category.
        Creates a new processing step if it doesn't exist.
        """
        existing_step = self.get_by_name_and_category(name, category)
        if existing_step:
            return existing_step

        # Create new processing step if not found
        new_step = PipelineProcessingStep(name=name, category=category)
        return self.insert(new_step)
