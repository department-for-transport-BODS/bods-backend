"""
Tables prefixed data_quality_
SQLAlchemy Models
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import List

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Interval,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, validates
from sqlalchemy.sql import text

from .common import BaseSQLModel


class DataQualityReport(BaseSQLModel):
    """
    Data Quality Report Table Model
    """

    __tablename__ = "data_quality_report"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        server_default="0.0",
        nullable=False,
        kw_only=True,
        doc="Data quality score",
    )

    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        kw_only=True,
        doc="Creation timestamp",
    )

    revision_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        kw_only=True,
        doc="Reference to the associated dataset revision",
    )

    file: Mapped[str] = mapped_column(
        String(255),  # Adjust length as needed
        nullable=False,
        kw_only=True,
        doc="Path to the JSON file",
    )

    @validates("file")
    def validate_file(self, key: str, value: str) -> str:
        """
        Ensures the file extension is json
        """
        if not value.lower().endswith(".json"):
            raise ValueError("File must have a .json extension")
        return value


class DataQualityServicePatternStop(BaseSQLModel):
    __tablename__ = "data_quality_servicepatternstop"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    service_pattern_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        kw_only=True,
        doc="Reference to the associated service pattern",
    )

    stop_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("stop_point.id", ondelete="PROTECT"),
        nullable=False,
        kw_only=True,
        doc="Reference to the associated stop point",
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        kw_only=True,
        doc="Position of the stop in the service pattern",
    )

    # Unique constraint
    __table_args__ = (
        UniqueConstraint(
            "service_pattern_id",
            "stop_id",
            "position",
            name="uix_service_pattern_stop_unique",
        ),
    )


class DataQualityServicePatternServiceLink(BaseSQLModel):
    __tablename__ = "data_quality_servicepatternservicelink"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    service_pattern_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        kw_only=True,
        doc="Reference to the associated service pattern",
    )

    service_link_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        kw_only=True,
        doc="Reference to the associated service link",
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        kw_only=True,
        doc="Position of the service link in the service pattern",
    )


class DataQualityServiceLink(BaseSQLModel):
    __tablename__ = "data_quality_servicelink"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    ito_id: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
        kw_only=True,
        doc="Unique identifier from ITO",
    )

    geometry: Mapped[str | None] = mapped_column(
        Geometry("LINESTRING", srid=4326),
        nullable=True,
        kw_only=True,
        doc="Geometric representation of the service link",
    )

    from_stop_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        kw_only=True,
        doc="Reference to the origin stop point",
    )

    to_stop_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        kw_only=True,
        doc="Reference to the destination stop point",
    )


class DataQualityServicepattern(BaseSQLModel):
    __tablename__ = "data_quality_servicepattern"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    ito_id: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
        kw_only=True,
        doc="Unique identifier from ITO",
    )

    service_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        kw_only=True,
        doc="Reference to the associated service",
    )

    name: Mapped[str] = mapped_column(
        String(255), nullable=False, kw_only=True, doc="Name of the service pattern"
    )

    geometry: Mapped[str] = mapped_column(
        Geometry("LINESTRING", srid=4326),
        nullable=False,
        kw_only=True,
        doc="Geometric representation of the service pattern",
    )


class DataQualityTimingPattern(BaseSQLModel):
    __tablename__ = "data_quality_timingpattern"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    ito_id: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
        kw_only=True,
        doc="Unique identifier from ITO",
    )

    service_pattern_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        kw_only=True,
        doc="Reference to the associated service pattern",
    )


class DataQualityTimingPatternStop(BaseSQLModel):
    __tablename__ = "data_quality_timingpatternstop"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    timing_pattern_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        kw_only=True,
    )

    service_pattern_stop_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        kw_only=True,
    )

    arrival: Mapped[timedelta] = mapped_column(
        Interval,
        nullable=False,
        kw_only=True,
        doc="The duration of time from the Vehicle Journey start time to reach service_pattern_stop",
    )

    departure: Mapped[timedelta] = mapped_column(
        Interval,
        nullable=False,
        kw_only=True,
        doc="The duration of time from the Vehicle Journey start time to depart service_pattern_stop",
    )

    pickup_allowed: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False, kw_only=True
    )

    setdown_allowed: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False, kw_only=True
    )

    timing_point: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False, kw_only=True
    )


class DataQualityStopPoint(BaseSQLModel):
    __tablename__ = "data_quality_stoppoint"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    ito_id: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
        kw_only=True,
        doc="Unique identifier from ITO",
    )

    atco_code: Mapped[str] = mapped_column(
        String(20), nullable=False, kw_only=True, doc="ATCO code identifier"
    )

    is_provisional: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        kw_only=True,
        doc="The stop is provisional and not yet officially in NapTaN",
    )

    name: Mapped[str] = mapped_column(
        String(255), nullable=False, kw_only=True, doc="Name of the stop point"
    )

    type: Mapped[str] = mapped_column(
        String(10), nullable=False, kw_only=True, doc="Type of stop point"
    )

    bearing: Mapped[int] = mapped_column(
        Integer, nullable=False, kw_only=True, doc="Bearing of the stop point"
    )

    geometry: Mapped[str] = mapped_column(
        Geometry("POINT", srid=4326),
        nullable=False,
        kw_only=True,
        doc="Geographic location of the stop point",
    )


class DataQualityVehicleJourney(BaseSQLModel):
    __tablename__ = "data_quality_vehiclejourney"

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
