from __future__ import annotations

from enum import Enum
from typing import Optional

from sqlalchemy import (Boolean, DateTime, ForeignKey, Integer, String, Text,
                        func)
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel, TimeStampedMixin


class DQSTaskState(str, Enum):
    """DQS Task states enum"""

    PENDING = "PENDING"
    
class DQSReport(TimeStampedMixin, BaseSQLModel):
    __tablename__ = 'dqs_report'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    revision_id: Mapped[int] = mapped_column(Integer, ForeignKey("organisation_datasetrevision.id"), nullable=False)
    status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now()) 
    file_name: Mapped[str] = mapped_column(String(255), nullable=True, default="")

class DQSChecks(TimeStampedMixin, BaseSQLModel):
    __tablename__ = 'dqs_checks'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    observation: Mapped[str] = mapped_column(String(1024))
    importance: Mapped[str] = mapped_column(String(64))
    category: Mapped[str] = mapped_column(String(64))
    queue_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)


class DQSTaskResults(TimeStampedMixin, BaseSQLModel):
    __tablename__ = 'dqs_task_results'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(64))
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    checks_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('dqs_checks.id'), nullable=False)
    dataquality_report_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('dqs_report.id'), nullable=False)
    transmodel_txcfileattributes_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('organisation_txcfileattributes.id'), nullable=False)
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    modified: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class DQSObservationResults(TimeStampedMixin, BaseSQLModel):
    __tablename__ = 'dqs_observation_results'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_suppressed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    taskresults_id: Mapped[int] = mapped_column(Integer, ForeignKey('dqs_task_results.id'), nullable=False)
    vehicle_journey_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('transmodel_vehiclejourney'), nullable=True)
    service_pattern_stop_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('transmodel_servicepattern'), nullable=True)
    serviced_organisation_vehicle_journey_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('transmodel_servicedorganisationvehiclejourney'), nullable=True)

