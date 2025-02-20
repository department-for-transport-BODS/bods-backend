"""
Models for Many to Many Relationhip Tables
AKA: Associative Entity, Junction Tables, Jump Tables
"""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel


class TransmodelServiceServicePattern(BaseSQLModel):
    """
    Association table between:
        - transmodel_service (TransmodelService)
        - transmodel_servicepattern (TransmodelServicePattern)
    """

    __tablename__ = "transmodel_service_service_patterns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    service_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transmodel_service.id", ondelete="CASCADE"), nullable=False
    )
    servicepattern_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("transmodel_servicepattern.id", ondelete="CASCADE"),
        nullable=False,
    )


class TransmodelServicePatternLocality(BaseSQLModel):
    """
    Association table between:
        - transmodel_servicepattern (TransmodelServicePattern)
        - naptan_locality (NaptanLocality)
    """

    __tablename__ = "transmodel_servicepattern_localities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    servicepattern_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("transmodel_servicepattern.id", ondelete="CASCADE"),
        nullable=False,
    )
    locality_id: Mapped[str] = mapped_column(String(8), nullable=False)


class TransmodelServicePatternAdminAreas(BaseSQLModel):
    """
    Association Table between:
        - transmodel_servicepattern (TransmodelServicePattern)
        - naptan_adminarea (NaptanAdminArea)
    """

    __tablename__ = "transmodel_servicepattern_admin_areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    servicepattern_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("transmodel_servicepattern.id", ondelete="CASCADE"),
        nullable=False,
    )
    adminarea_id: Mapped[int] = mapped_column(Integer, nullable=False)


class TransmodelTracksVehicleJourney(BaseSQLModel):
    """
    Association table between Tracks and Vehicle Journeys
    Represents which tracks are used by which vehicle journeys in sequence
    """

    __tablename__ = "transmodel_tracksvehiclejourney"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, init=False, autoincrement=True
    )
    sequence_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tracks_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("transmodel_tracks.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
    )
    vehicle_journey_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "transmodel_vehiclejourney.id", deferrable=True, initially="DEFERRED"
        ),
        nullable=False,
    )
