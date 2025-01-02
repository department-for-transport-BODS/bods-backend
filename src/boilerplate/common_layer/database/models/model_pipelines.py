"""
SQL Alchemy models for tables starting with pipelines_
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel, TimeStampedMixin


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
        SQLEnum(TaskState),
        index=True,
        default=TaskState.PENDING,
        kw_only=True,
        doc="Current state of the task being run",
    )

    completed: Mapped[Optional[datetime]] = mapped_column(
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


class ETLErrorCode(str, Enum):
    """Error codes for ETL tasks"""

    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    ZIP_TOO_LARGE = "ZIP_TOO_LARGE"
    NESTED_ZIP_FORBIDDEN = "NESTED_ZIP_FORBIDDEN"
    NO_DATA_FOUND = "NO_DATA_FOUND"
    XML_SYNTAX_ERROR = "XML_SYNTAX_ERROR"
    DANGEROUS_XML_ERROR = "DANGEROUS_XML_ERROR"
    SCHEMA_VERSION_MISSING = "SCHEMA_VERSION_MISSING"
    SCHEMA_VERSION_NOT_SUPPORTED = "SCHEMA_VERSION_NOT_SUPPORTED"
    SCHEMA_ERROR = "SCHEMA_ERROR"
    POST_SCHEMA_ERROR = "POST_SCHEMA_ERROR"
    DATASET_EXPIRED = "DATASET_EXPIRED"
    SUSPICIOUS_FILE = "SUSPICIOUS_FILE"
    NO_VALID_FILE_TO_PROCESS = "NO_VALID_FILE_TO_PROCESS"
    ANTIVIRUS_FAILURE = "ANTIVIRUS_FAILURE"
    AV_CONNECTION_ERROR = "AV_CONNECTION_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"


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

    error_code: Mapped[Optional[ETLErrorCode]] = mapped_column(
        SQLEnum(ETLErrorCode),
        nullable=False,
        index=True,
        default="",
        kw_only=True,
        doc="The error code returned for the failed task",
    )

    additional_info: Mapped[Optional[str]] = mapped_column(
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
        Integer, ForeignKey("public.pipelines_pipelineerrorcode.id"), nullable=True
    )

    pipeline_processing_step_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("public.pipelines_pipelineprocessingstep.id"),
        nullable=False,
    )

    revision_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("public.organisation_datasetrevision.id"), nullable=False
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
