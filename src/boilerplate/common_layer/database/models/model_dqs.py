"""
SQLAlchemy models for dqs
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel


class DQSTaskResults(BaseSQLModel):
    """DQS Task Results Table"""

    __tablename__ = "dqs_taskresults"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    modified: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    transmodel_txcfileattributes_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "organisation_txcfileattributes.id", deferrable=True, initially="DEFERRED"
        ),
        nullable=True,
    )
