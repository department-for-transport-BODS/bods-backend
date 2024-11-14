"""
SQL Alchemy models for tables starting with transmodel_
"""

from __future__ import annotations

from datetime import date, time
from typing import List, Optional

from sqlalchemy import Date, ForeignKey, Integer, String, Text, Time
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from timetables_etl.app.database.models.model_data_quality import (
    DataQualityTimingPattern,
)

from .common import BaseSQLModel
from .model_organisation import (
    OrganisationDatasetrevision,
    OrganisationTxcFileAttributes,
)


class TransmodelService(BaseSQLModel):
    __tablename__ = "transmodel_service"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    service_code: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    other_names: Mapped[list[str]] = mapped_column(ARRAY(String(255)), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    service_type: Mapped[str] = mapped_column(String(255), nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    revision_id: Mapped[Optional[int]] = mapped_column(Integer)
    txcfileattributes_id: Mapped[Optional[int]] = mapped_column(Integer)

    revision: Mapped["OrganisationDatasetrevision"] = relationship(
        "OrganisationDatasetrevision", back_populates="transmodel_service", init=False
    )
    txcfileattributes: Mapped["OrganisationTxcFileAttributes"] = relationship(
        "OrganisationTxcfileattributes", back_populates="transmodel_service", init=False
    )


class TransmodelVehicleJourney(BaseSQLModel):
    __tablename__ = "transmodel_vehiclejourney"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    ito_id: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
        kw_only=True,
        doc="Unique identifier from ITO",
    )

    timing_pattern_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("timing_pattern.id", ondelete="CASCADE"),
        nullable=False,
        kw_only=True,
        doc="Reference to the associated timing pattern",
    )

    start_time: Mapped[time] = mapped_column(
        Time, nullable=False, kw_only=True, doc="Start time of the vehicle journey"
    )

    dates: Mapped[List[date]] = mapped_column(
        ARRAY(Date),
        nullable=False,
        default_factory=list,
        kw_only=True,
        doc="List of dates for this vehicle journey",
    )

    # Relationships
    timing_pattern: Mapped["DataQualityTimingPattern"] = relationship(
        "DataQualityTimingPattern",
        back_populates="vehicle_journeys",
        default=None,
        kw_only=True,
    )
