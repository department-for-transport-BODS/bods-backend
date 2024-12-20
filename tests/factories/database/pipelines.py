"""
Factories for tables prefixed pipelines_
"""

from datetime import UTC, datetime

import factory
from common_layer.database.models.model_pipelines import DatasetETLTaskResult, TaskState
from factory import LazyFunction
from factory.fuzzy import FuzzyInteger


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
