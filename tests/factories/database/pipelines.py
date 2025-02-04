"""
Factories for tables prefixed pipelines_
"""

from datetime import UTC, datetime
from uuid import uuid4

import factory
from common_layer.database.models.model_pipelines import (
    DatasetETLTaskResult,
    ETLErrorCode,
    FileProcessingResult,
    PipelineErrorCode,
    PipelineProcessingStep,
    TaskState,
)
from factory import LazyFunction
from factory.fuzzy import FuzzyChoice, FuzzyInteger, FuzzyText


class DatasetETLTaskResultFactory(factory.Factory):
    """
    Factory for DatasetETLTaskResult
    """

    class Meta:  # type: ignore[misc]
        """Factory configuration."""

        model = DatasetETLTaskResult

    task_id = factory.Sequence(lambda n: f"task_{n}")
    status = TaskState.PENDING
    completed = None
    revision_id = FuzzyInteger(1000, 5000)
    progress = 0
    task_name_failed = ""
    error_code = None
    additional_info = None
    created = LazyFunction(lambda: datetime.now(UTC))
    modified = LazyFunction(lambda: datetime.now(UTC))

    @classmethod
    def create_with_id(cls, id_number: int, **kwargs) -> DatasetETLTaskResult:
        """Creates a task result with a specific ID"""
        task_result = cls.create(**kwargs)
        task_result.id = id_number
        return task_result

    @classmethod
    def create_for_revision(cls, revision_id: int, **kwargs) -> DatasetETLTaskResult:
        """Creates a task result for a specific revision"""
        return cls.create(revision_id=revision_id, **kwargs)


class PipelineErrorCodeFactory(factory.Factory):
    """Factory for PipelineErrorCode"""

    class Meta:  # type: ignore[misc]
        model = PipelineErrorCode

    error = FuzzyChoice([e.value for e in ETLErrorCode])


class PipelineProcessingStepFactory(factory.Factory):
    """Factory for PipelineProcessingStep"""

    class Meta:  # type: ignore[misc]
        model = PipelineProcessingStep

    name = FuzzyText(prefix="step_", length=20)
    category = FuzzyChoice(["TIMETABLES", "FARES"])


class FileProcessingResultFactory(factory.Factory):
    """Factory for FileProcessingResult"""

    class Meta:  # type: ignore[misc]
        model = FileProcessingResult

    task_id = factory.LazyFunction(lambda: str(uuid4()))
    filename = factory.Sequence(lambda n: f"test_file_{n}.xml")
    status = FuzzyChoice(list(TaskState))
    pipeline_processing_step_id = factory.LazyFunction(
        lambda: PipelineProcessingStepFactory().id
    )
    revision_id = FuzzyInteger(1000, 5000)
    error_message = None
    pipeline_error_code_id = None
    completed = None

    @classmethod
    def create_pending(cls, **kwargs) -> FileProcessingResult:
        """Creates a FileProcessingResult in PENDING state"""
        return cls.create(
            status=TaskState.PENDING,
            completed=None,
            error_message=None,
            pipeline_error_code_id=None,
            **kwargs,
        )

    @classmethod
    def create_started(cls, **kwargs) -> FileProcessingResult:
        """Creates a FileProcessingResult in STARTED state"""
        return cls.create(
            status=TaskState.STARTED,
            completed=None,
            error_message=None,
            pipeline_error_code_id=None,
            **kwargs,
        )

    @classmethod
    def create_success(cls, **kwargs) -> FileProcessingResult:
        """Creates a FileProcessingResult in SUCCESS state with completion time"""
        return cls.create(
            status=TaskState.SUCCESS,
            completed=datetime.now(UTC),
            error_message=None,
            pipeline_error_code_id=None,
            **kwargs,
        )

    @classmethod
    def create_failure(
        cls, error_message: str = "Test error", **kwargs
    ) -> FileProcessingResult:
        """Creates a FileProcessingResult in FAILURE state with error details"""
        error_code = PipelineErrorCodeFactory()
        return cls.create(
            status=TaskState.FAILURE,
            completed=datetime.now(UTC),
            error_message=error_message,
            pipeline_error_code_id=error_code.id,
            **kwargs,
        )

    @classmethod
    def create_with_error(
        cls, error_code: ETLErrorCode, error_message: str = "Test error", **kwargs
    ) -> FileProcessingResult:
        """Creates a FileProcessingResult with a specific error code"""
        error = PipelineErrorCodeFactory(error=error_code.value)
        return cls.create(
            status=TaskState.FAILURE,
            completed=datetime.now(UTC),
            error_message=error_message,
            pipeline_error_code_id=error.id,
            **kwargs,
        )

    @classmethod
    def create_batch(cls, size: int, **kwargs) -> list[FileProcessingResult]:
        """Creates multiple FileProcessingResults with sequential task IDs"""
        return [cls.create(**kwargs) for _ in range(size)]
