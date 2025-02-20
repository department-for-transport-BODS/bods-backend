"""
SQL Alchemy models for tables starting with transmodel_
"""

from __future__ import annotations

from datetime import date, time
from typing import TYPE_CHECKING, Literal

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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .common import BaseSQLModel

if TYPE_CHECKING:
    from .model_organisation import OrganisationTXCFileAttributes
    from .model_transmodel_flexible import TransmodelBookingArrangements
    from .model_transmodel_vehicle_journey import TransmodelVehicleJourney


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

    txcfileattributes_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("organisation_txcfileattributes.id", ondelete="CASCADE"),
        nullable=True,
    )

    txcfileattributes: Mapped["OrganisationTXCFileAttributes"] = relationship(
        "OrganisationTXCFileAttributes",
        back_populates="transmodel_services",
        cascade="all, delete",
        init=False,
    )

    booking_arrangements: Mapped[list["TransmodelBookingArrangements"]] = relationship(
        "TransmodelBookingArrangements",
        back_populates="service",
        cascade="all, delete",
        init=False,
    )

    service_patterns: Mapped[list["TransmodelServicePattern"]] = relationship(
        "TransmodelServicePattern",
        secondary="transmodel_service_service_patterns",
        back_populates="services",
        cascade="all, delete",
        init=False,
    )


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

    services: Mapped[list["TransmodelService"]] = relationship(
        "TransmodelService",
        secondary="transmodel_service_service_patterns",
        back_populates="service_patterns",
        init=False,
    )

    vehicle_journeys: Mapped[list["TransmodelVehicleJourney"]] = relationship(
        "TransmodelVehicleJourney",
        back_populates="servicepattern",
        cascade="all, delete",
    )


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
    servicepattern_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("transmodel_servicepattern.id", ondelete="CASCADE"),
        nullable=False,
    )
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

    __table_args__ = (
        UniqueConstraint(
            "from_atco_code", "to_atco_code", name="unique_from_to_atco_code"
        ),
    )
