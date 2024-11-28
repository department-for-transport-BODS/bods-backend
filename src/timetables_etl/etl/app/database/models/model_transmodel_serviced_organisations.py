"""
Transmodel Serviced Organisation Models
"""

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel


class TransmodelServicedOrganisations(BaseSQLModel):
    """Transmodel Serviced Organisations Table"""

    __tablename__ = "transmodel_servicedorganisations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    organisation_code: Mapped[str | None] = mapped_column(String(255), nullable=True)


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
