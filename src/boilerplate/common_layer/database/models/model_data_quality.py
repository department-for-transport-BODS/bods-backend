"""
SQL Alchemy models for tables starting with data_quality
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel


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
