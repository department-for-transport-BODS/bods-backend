"""
Transmodel Tables for handling Flexible Services
"""

from datetime import datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .common import BaseSQLModel

if TYPE_CHECKING:
    from .model_transmodel import TransmodelService


class TransmodelFlexibleServiceOperationPeriod(BaseSQLModel):
    """Transmodel Flexible Service Operation Period Table"""

    __tablename__ = "transmodel_flexibleserviceoperationperiod"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    vehicle_journey_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transmodel_vehiclejourney.id"), nullable=False
    )
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)


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

    service: Mapped["TransmodelService"] = relationship(
        "TransmodelService", back_populates="booking_arrangements", init=False
    )
