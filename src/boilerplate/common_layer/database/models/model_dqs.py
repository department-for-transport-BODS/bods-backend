"""
SQLAlchemy models for dqs
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .common import BaseSQLModel

if TYPE_CHECKING:
    from .model_organisation import OrganisationTXCFileAttributes


class DQSReport(BaseSQLModel):
    """DQS Report Table"""

    __tablename__ = "dqs_report"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=True)

    revision_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "organisation_datasetrevision.id", deferrable=True, initially="DEFERRED"
        ),
        nullable=False,
    )

    dqs_task_results: Mapped[list["DQSTaskResults"]] = relationship(
        "DQSTaskResults",
        back_populates="dataquality_report",
        init=False,
    )


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
            "organisation_txcfileattributes.id",
            deferrable=True,
            initially="DEFERRED",
        ),
        nullable=True,
    )

    transmodel_txcfileattributes: Mapped["OrganisationTXCFileAttributes"] = (
        relationship(
            "OrganisationTXCFileAttributes",
            back_populates="dqs_task_results",
            # cascade="all, delete",  # Automatically delete dependent records
        )
    )

    dataquality_report_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "dqs_report.id", deferrable=True, initially="DEFERRED", ondelete="cascade"
        ),
        nullable=True,
    )

    dataquality_report: Mapped[DQSReport] = relationship(
        DQSReport,
        back_populates="dqs_task_results",
        cascade="all, delete",  # Automatically delete dependent records
    )
