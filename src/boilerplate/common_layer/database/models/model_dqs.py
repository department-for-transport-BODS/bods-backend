from __future__ import annotations

from enum import Enum
from typing import List, Optional

from sqlalchemy import (Boolean, DateTime, ForeignKey, Integer, String, Text,
                        func)
from sqlalchemy.orm import Mapped, mapped_column

from ..models import OrganisationDatasetRevision
from .common import BaseSQLModel, TimeStampedMixin


class DQSTaskState(str, Enum):
    """DQS Task states enum"""

    PENDING = "PENDING"
    
class DQSReport(TimeStampedMixin, BaseSQLModel):
    __tablename__ = 'dqs_report'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    file_name: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    revision_id: Mapped[int] = mapped_column(Integer, nullable=False)

    @classmethod
    def initialise_dqs_task(cls, session, revision: OrganisationDatasetRevision) -> "DQSReport":
        """
        Create a new DQSReport instance with the provided data and save it to the database.
        """
        existing_report = session.query(cls).filter_by(revision_id=revision.id).first()
        if existing_report:
            session.delete(existing_report)

        new_report = cls(
            file_name="", revision=revision, status="PIPELINE_PENDING"
        )
        session.add(new_report)
        session.commit()
        return new_report


class DQSChecks(TimeStampedMixin, BaseSQLModel):
    __tablename__ = 'dqs_checks'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    observation: Mapped[str] = mapped_column(String(1024))
    importance: Mapped[str] = mapped_column(String(64))
    category: Mapped[str] = mapped_column(String(64))
    queue_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    @classmethod
    def get_all_checks(cls, session) -> List["DQSChecks"]:
        """
        Fetches all checks in the database
        """
        return session.query(cls).all()


class DQSTaskResults(TimeStampedMixin, BaseSQLModel):
    __tablename__ = 'dqs_task_results'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    modified: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    status: Mapped[str] = mapped_column(String(64))
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    checks_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('checks.id'), nullable=True)
    dataquality_report_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('reports.id'), nullable=True)
    transmodel_txcfileattributes_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=False)

    @classmethod
    def initialize_task_results(
        cls, session, report: "DQSReport", combinations: List[tuple]
    ) -> List:
    # ) -> object:
        """
        Create a TaskResults object based on the given revision, TXCFileAttribute,
        and Check objects.
        """
        task_results_to_create = [
            cls(
                status="PENDING",
                message="",
                checks=check,
                dataquality_report=report,
                transmodel_txcfileattributes=txc_file_attribute,
            )
            for txc_file_attribute, check in combinations
        ]

        session.add_all(task_results_to_create)
        session.commit()
        return task_results_to_create


class DQSObservationResults(TimeStampedMixin, BaseSQLModel):
    __tablename__ = 'dqs_observation_results'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_suppressed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    taskresults_id: Mapped[int] = mapped_column(Integer, ForeignKey('task_results.id'))
    vehicle_journey_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=False)
    service_pattern_stop_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=False)
    serviced_organisation_vehicle_journey_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=False)
    
    @classmethod
    def get_all_observation_results(cls, session) -> List["DQSObservationResults"]:
        """
        Fetches all observation results in the database
        """
        return session.query(cls).all()

