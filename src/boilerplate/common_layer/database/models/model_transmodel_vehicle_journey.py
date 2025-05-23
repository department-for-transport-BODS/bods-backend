"""
TM Vehicle Journey Models
"""

from datetime import date, time
from enum import Enum

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel


class TMDayOfWeek(str, Enum):
    """
    Days of the Wek Enum for transmodel_operating profile
    """

    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


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


class TransmodelOperatingProfile(BaseSQLModel):
    """Transmodel Operating Profile Table"""

    __tablename__ = "transmodel_operatingprofile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    day_of_week: Mapped[TMDayOfWeek] = mapped_column(String(20), nullable=False)
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
