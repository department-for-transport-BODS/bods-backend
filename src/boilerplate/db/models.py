"""
Description: Module containing all database models used in boilerplate/backend.
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Enum,
    func,
    ForeignKey,
    relationship,
)
from sqlalchemy.ext.declarative import declarative_base

# Define the base for declarative classes
Base = declarative_base()


class StatusEnum(Enum):
    ERROR    = "ERROR" # noqa
    FAILURE  = "FAILURE" # noqa
    PENDING  = "PENDING" # noqa
    READY    = "READY" # noqa
    RECEIVED = "RECEIVED"
    STARTED  = "STARTED" # noqa
    SUCCESS  = "SUCCESS" # noqa


class PipelineErrorCode(Base):
    __tablename__ = "pipeline_error_code"  # noqa

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String(255))


class PipelineProcessingStep(Base):
    __tablename__ = "pipeline_processing_step" # noqa
    id   = Column(Integer, primary_key=True, autoincrement=True) # noqa
    name = Column(String(20))


class FileProcessingResult(Base):
    __tablename__ = "file_processing_result"  # noqa

    id = Column(Integer, primary_key=True, autoincrement=True)
    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), server_default=func.now())
    task_id = Column(String(36))
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING)
    completed = Column(DateTime(timezone=True), nullable=True)
    filename = Column(String(255))
    error_message = Column(Text, nullable=True)
    pipeline_error_code = Column(Integer, ForeignKey('pipeline_error_code.id'), nullable=False)
    pipeline_processing_step = Column(Integer, ForeignKey('pipeline_processing_step.id'), nullable=False)
    revision = Column(Integer, ForeignKey("organisation_datasetrevision.id"), nullable=False) # noqa

    # Relationships
    error_code = relationship("pipeline_error_code")
    processing_step = relationship("pipeline_processing_step")
    dataset_revision = relationship("organisation_datasetrevision") # noqa