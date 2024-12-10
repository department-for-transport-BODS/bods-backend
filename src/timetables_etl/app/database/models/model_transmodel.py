"""
SQL Alchemy models for tables starting with transmodel_
"""

from __future__ import annotations

from datetime import date, datetime, time

from geoalchemy2 import Geometry, WKBElement
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Time
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
    service_type: Mapped[str] = mapped_column(String(255), nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    revision_id: Mapped[int | None] = mapped_column(Integer)
    txcfileattributes_id: Mapped[int | None] = mapped_column(Integer)


class TransmodelVehicleJourney(BaseSQLModel):
    """
    Transmodel Vehicle Journey Table
    Each TXC Vehicle journey has a mapping to a Transmodel Service Pattern
    """

    __tablename__ = "transmodel_vehiclejourney"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    direction: Mapped[str | None] = mapped_column(String(255), nullable=True)
    journey_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    line_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    departure_day_shift: Mapped[bool] = mapped_column(Boolean, nullable=False)
    service_pattern_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    block_number: Mapped[str | None] = mapped_column(String(20), nullable=True)


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
    geom: Mapped[WKBElement] = mapped_column(
        Geometry("LINESTRING", 4326), nullable=True
    )
    revision_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_name: Mapped[str | None] = mapped_column(String(255), nullable=True)


class TransmodelServicedOrganisations(BaseSQLModel):
    """Transmodel Serviced Organisations Table"""

    __tablename__ = "transmodel_servicedorganisations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    organisation_code: Mapped[str | None] = mapped_column(String(255), nullable=True)


class TransmodelFlexibleServiceOperationPeriod(BaseSQLModel):
    """Transmodel Flexible Service Operation Period Table"""

    __tablename__ = "transmodel_flexibleserviceoperationperiod"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    vehicle_journey_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transmodel_vehiclejourney.id"), nullable=False
    )
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)


class TransmodelOperatingProfile(BaseSQLModel):
    """Transmodel Operating Profile Table"""

    __tablename__ = "transmodel_operatingprofile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    day_of_week: Mapped[str] = mapped_column(String(20), nullable=False)
    vehicle_journey_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transmodel_vehiclejourney.id"), nullable=False
    )


class TransmodelOperatingDatesExceptions(BaseSQLModel):
    """Transmodel Operating Dates Exceptions Table"""

    __tablename__ = "transmodel_operatingdatesexceptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    operating_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    vehicle_journey_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transmodel_vehiclejourney.id"), nullable=False
    )


class TransmodelNonOperatingDatesExceptions(BaseSQLModel):
    """Transmodel Non Operating Dates Exceptions Table"""

    __tablename__ = "transmodel_nonoperatingdatesexceptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    non_operating_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    vehicle_journey_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transmodel_vehiclejourney.id"), nullable=False
    )


class TransmodelServicedOrganisationVehicleJourney(BaseSQLModel):
    """Transmodel Serviced Organisation Vehicle Journey Table"""

    __tablename__ = "transmodel_servicedorganisationvehiclejourney"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    operating_on_working_days: Mapped[bool] = mapped_column(Boolean, nullable=False)
    serviced_organisation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transmodel_servicedorganisations.id"), nullable=False
    )
    vehicle_journey_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transmodel_vehiclejourney.id"), nullable=False
    )


class TransmodelServicedOrganisationWorkingDays(BaseSQLModel):
    """Transmodel Serviced Organisation Working Days Table"""

    __tablename__ = "transmodel_servicedorganisationworkingdays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    serviced_organisation_vehicle_journey_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("transmodel_servicedorganisationvehiclejourney.id"),
        nullable=True,
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
    service_pattern_id: Mapped[int] = mapped_column(Integer, nullable=False)
    departure_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    is_timing_point: Mapped[bool] = mapped_column(Boolean, nullable=False)
    txc_common_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vehicle_journey_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stop_activity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    auto_sequence_number: Mapped[int | None] = mapped_column(Integer, nullable=True)


class TransmodelBookingArrangements(BaseSQLModel):
    """Transmodel Booking Arrangements Table"""

    __tablename__ = "transmodel_bookingarrangements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(16), nullable=True)
    web_address: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    service_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transmodel_service.id"), nullable=False
    )


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
