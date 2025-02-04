"""
SQL Alchemy models for tables starting with data_quality
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel, TimeStampedMixin


class DataQualitySchemaViolation(BaseSQLModel):
    """Data Quality Schema Violation Table"""

    __tablename__ = "data_quality_schemaviolation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    line: Mapped[int] = mapped_column(Integer, nullable=False)
    details: Mapped[str] = mapped_column(String(1024), nullable=False)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revision_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "organisation_datasetrevision.id", deferrable=True, initially="DEFERRED"
        ),
        nullable=False,
    )


class DataQualityPostSchemaViolation(BaseSQLModel):
    """Data Quality Post Schema Violation Table"""

    __tablename__ = "data_quality_postschemaviolation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    details: Mapped[str] = mapped_column(String(1024), nullable=False)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revision_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "organisation_datasetrevision.id", deferrable=True, initially="DEFERRED"
        ),
        nullable=False,
    )


class DataQualityPTIObservation(TimeStampedMixin, BaseSQLModel):
    """Data Quality PTI Observation Table"""

    include_modified = False

    __tablename__ = "data_quality_ptiobservation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    filename: Mapped[str] = mapped_column(String(256))
    line: Mapped[int] = mapped_column(Integer)
    details: Mapped[str] = mapped_column(String(1024))
    element: Mapped[str] = mapped_column(String(256))
    category: Mapped[str] = mapped_column(String(1024))
    revision_id: Mapped[int] = mapped_column(Integer)
    reference: Mapped[str] = mapped_column(String(64))
