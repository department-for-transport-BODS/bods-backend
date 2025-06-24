"""
SQL Alchemy models for tables starting with transmodel_
"""

from __future__ import annotations

from datetime import date, time
from typing import Literal

from geoalchemy2 import Geometry, WKBElement
from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel


class TransmodelService(BaseSQLModel):
    """
    Transmodel Service Table
    Each Service in a TXC file is an instance of this
    PTI states there should only be one per file
    """

    __tablename__ = "transmodel_service"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    service_code: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    other_names: Mapped[list[str]] = mapped_column(ARRAY(String(255)), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    service_type: Mapped[Literal["standard", "flexible"]] = mapped_column(
        String(255), nullable=False
    )
    end_date: Mapped[date | None] = mapped_column(Date)
    revision_id: Mapped[int | None] = mapped_column(Integer)
    txcfileattributes_id: Mapped[int | None] = mapped_column(Integer)


class TransmodelServicePattern(BaseSQLModel):
    """
    Transmodel Service Pattern Table

    The geom field uses SRID 4326 (WGS84) which is Longitude / Latitude
    """

    __tablename__ = "transmodel_servicepattern"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    service_pattern_id: Mapped[str] = mapped_column(String(255), nullable=False)
    origin: Mapped[str] = mapped_column(String(255), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    geom: Mapped[WKBElement | None] = mapped_column(
        Geometry("LINESTRING", 4326), nullable=True
    )
    revision_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_name: Mapped[str | None] = mapped_column(String(255), nullable=True)


class TransmodelServicePatternStop(BaseSQLModel):
    """
    Transmodel Service Pattern Stop Table
    Each Row is a stop for a particular vehicle journey
    """

    __tablename__ = "transmodel_servicepatternstop"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    atco_code: Mapped[str] = mapped_column(String(255), nullable=False)
    naptan_stop_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    service_pattern_id: Mapped[int] = mapped_column(Integer, nullable=False)
    departure_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    is_timing_point: Mapped[bool] = mapped_column(Boolean, nullable=False)
    txc_common_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vehicle_journey_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stop_activity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    auto_sequence_number: Mapped[int | None] = mapped_column(Integer, nullable=True)


class TransmodelStopActivity(BaseSQLModel):
    """
    Transmodel Stop Activity Table
    Can't guarantee the order, so need to fetch and reference when making stop points
    """

    __tablename__ = "transmodel_stopactivity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_pickup: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_setdown: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_driverrequest: Mapped[bool] = mapped_column(Boolean, nullable=False)


class TransmodelBankHolidays(BaseSQLModel):
    """
    Transmodel Bank Holidays Table
    List of Bank Holidays which is used as a reference to
    """

    __tablename__ = "transmodel_bankholidays"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, init=False, autoincrement=True
    )
    txc_element: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    division: Mapped[str | None] = mapped_column(String(255), nullable=True)


class TransmodelTracks(BaseSQLModel):
    """
    Transmodel Track Table
    Represents a track segment between two stops with geometry and distance
    """

    __tablename__ = "transmodel_tracks"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, init=False, autoincrement=True
    )
    from_atco_code: Mapped[str] = mapped_column(String(255), nullable=False)
    to_atco_code: Mapped[str] = mapped_column(String(255), nullable=False)
    geometry: Mapped[WKBElement | None] = mapped_column(
        Geometry("LINESTRING", 4326), nullable=True
    )
    distance: Mapped[int | None] = mapped_column(Integer, nullable=True)


class TransmodelServicePatternDistance(BaseSQLModel):
    """
    Transmodel ServicePatternDistance table
    Represents a track segment between two stops with geometry and distance
    """

    __tablename__ = "transmodel_servicepatterndistance"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, init=False, autoincrement=True
    )
    geom: Mapped[WKBElement | None] = mapped_column(
        Geometry("LINESTRING", 4326), nullable=True
    )
    distance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # pylint: disable=duplicate-code
    service_pattern_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "transmodel_servicepattern.id", deferrable=True, initially="DEFERRED"
        ),
        nullable=False,
    )
