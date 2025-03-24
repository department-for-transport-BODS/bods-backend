"""
SQL Alchemy models for tables starting with pipelines_
"""

# pylint: disable=too-many-ancestors

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import DateTime, Dialect
from sqlalchemy import Enum as SqlAlchemyEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from .common import BaseSQLModel, TimeStampedMixin
from .error_codes import ETLErrorCode


class TaskState(str, Enum):
    """Task states enum"""

    PENDING = "PENDING"
    RECEIVED = "RECEIVED"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    READY = "READY"


class TaskResult(TimeStampedMixin, BaseSQLModel):
    """
    Base class for task results that mirrors Django's celery-like task results.
    This is an abstract base class that can be inherited from.
    """

    __abstract__ = True

    task_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        default=None,
        kw_only=True,
        doc="The ID for the Task that was run",
    )

    status: Mapped[TaskState] = mapped_column(
        String(50),
        index=True,
        default=TaskState.PENDING.value,
        kw_only=True,
        doc="Current state of the task being run",
    )

    completed: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
        default=None,
        nullable=True,
        kw_only=True,
        doc="Datetime field when the task was completed in UTC",
    )

    def to_success(self) -> None:
        """Mark the task as successful and set completion time"""
        self.status = TaskState.SUCCESS
        self.completed = datetime.now(UTC)

    def to_error(self) -> None:
        """Mark the task as failed and set completion time"""
        self.status = TaskState.FAILURE
        self.completed = datetime.now(UTC)


class ETLErrorCodeType(TypeDecorator[ETLErrorCode]):
    """Custom type that converts empty strings to ETLErrorCode.EMPTY"""

    impl = SqlAlchemyEnum
    cache_ok = True

    def __init__(self, **kw: Any) -> None:
        # Ensure empty string is explicitly included in the enum values
        if "values_callable" in kw:
            original_callable = kw["values_callable"]
            kw["values_callable"] = lambda e: original_callable(e) + [""]  # type: ignore
        else:
            kw["values_callable"] = lambda e: [x.name for x in e] + [""]  # type: ignore

        kw["validate_strings"] = False

        super().__init__(**kw)

    def process_result_value(self, value: Any | None, dialect: Dialect) -> ETLErrorCode:
        """Convert from DB to Python"""
        if value == "" or value is None:
            return ETLErrorCode.EMPTY
        try:
            result = super().process_result_value(value, dialect)
            return ETLErrorCode.EMPTY if result is None else result
        except LookupError:
            # Catch lookup errors and return EMPTY
            return ETLErrorCode.EMPTY

    def process_bind_param(self, value: ETLErrorCode | None, dialect: Dialect) -> str:
        """Convert from Python to DB"""
        if value is None or value is ETLErrorCode.EMPTY:
            return ""
        return str(value.value)

    def process_literal_param(self, value: Any | None, dialect: Dialect) -> str:
        """Process literal parameter values"""
        if value == "" or value is None:
            return "''"  # SQL literal for empty string
        return str(value)

    @property
    def python_type(self) -> type[ETLErrorCode]:
        """Return the Python type this is bound to"""
        return ETLErrorCode


class DatasetETLTaskResult(TaskResult):
    """ETL Task Result for Dataset processing"""

    __tablename__ = "pipelines_datasetetltaskresult"

    # Columns
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)

    revision_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        kw_only=True,
    )

    progress: Mapped[int] = mapped_column(Integer, default=0, kw_only=True)

    task_name_failed: Mapped[str] = mapped_column(String(255), default="", kw_only=True)

    error_code: Mapped[ETLErrorCode] = mapped_column(
        ETLErrorCodeType(
            enum_class=ETLErrorCode,
            native_enum=False,
            length=50,
        ),
        nullable=False,
        index=True,
        default=ETLErrorCode.EMPTY,
        kw_only=True,
        doc="The error code returned for the failed task",
    )

    additional_info: Mapped[str | None] = mapped_column(
        String(512), default=None, nullable=True, kw_only=True
    )


class FileProcessingResult(TaskResult):
    """Pipelines File Processing Result Table"""

    __tablename__ = "pipelines_fileprocessingresult"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, init=False, autoincrement=True
    )

    filename: Mapped[str] = mapped_column(String(255), nullable=False)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    pipeline_error_code_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("pipelines_pipelineerrorcode.id"), nullable=True
    )

    pipeline_processing_step_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pipelines_pipelineprocessingstep.id"),
        nullable=False,
    )

    revision_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organisation_datasetrevision.id"), nullable=False
    )


class PipelineErrorCode(BaseSQLModel):
    """
    Pipeline Error Code table representing predefined error codes
    """

    __tablename__ = "pipelines_pipelineerrorcode"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, init=False, autoincrement=True
    )

    error: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)


class PipelineProcessingStep(BaseSQLModel):
    """
    Pipeline Processing Step table representing different steps in ETL pipeline
    """

    __tablename__ = "pipelines_pipelineprocessingstep"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, init=False, autoincrement=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    category: Mapped[str] = mapped_column(String(20), nullable=False)
