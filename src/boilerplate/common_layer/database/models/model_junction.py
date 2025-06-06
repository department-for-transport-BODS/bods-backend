"""
Models for Many to Many Relationhip Tables
AKA: Associative Entity, Junction Tables, Jump Tables
"""

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
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
    service_id: Mapped[int] = mapped_column(Integer, nullable=False)
    servicepattern_id: Mapped[int] = mapped_column(Integer, nullable=False)


class TransmodelServicePatternLocality(BaseSQLModel):
    """
    Association table between:
        - transmodel_servicepattern (TransmodelServicePattern)
        - naptan_locality (NaptanLocality)
    """

    __tablename__ = "transmodel_servicepattern_localities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    servicepattern_id: Mapped[int] = mapped_column(Integer, nullable=False)
    locality_id: Mapped[str] = mapped_column(String(8), nullable=False)


class OrganisationDatasetRevisionLocalities(BaseSQLModel):
    """
    Association Table between:
        - organisation_datasetrevision (OrganisationDatasetRevision)
        - naptan_locality (NaptanLocality)
    """

    __tablename__ = "organisation_datasetrevision_localities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    datasetrevision_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "organisation_datasetrevision.id", deferrable=True, initially="DEFERRED"
        ),
        nullable=False,
    )
    locality_id: Mapped[str] = mapped_column(
        String(8),
        ForeignKey(
            "naptan_locality.gazetteer_id", deferrable=True, initially="DEFERRED"
        ),
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("datasetrevision_id", "locality_id"),)


class TransmodelServicePatternAdminAreas(BaseSQLModel):
    """
    Association Table between:
        - transmodel_servicepattern (TransmodelServicePattern)
        - naptan_adminarea (NaptanAdminArea)
    """

    __tablename__ = "transmodel_servicepattern_admin_areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    servicepattern_id: Mapped[int] = mapped_column(Integer, nullable=False)
    adminarea_id: Mapped[int] = mapped_column(Integer, nullable=False)


class OrganisationDatasetRevisionAdminAreas(BaseSQLModel):
    """
    Association Table between:
        - organisation_datasetrevision (OrganisationDatasetRevision)
        - naptan_adminarea (NaptanAdminArea)
    """

    __tablename__ = "organisation_datasetrevision_admin_areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    datasetrevision_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "organisation_datasetrevision.id", deferrable=True, initially="DEFERRED"
        ),
        nullable=False,
    )
    adminarea_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("naptan_adminarea.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("datasetrevision_id", "adminarea_id"),)


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


class TransmodelServicePatternTracks(BaseSQLModel):
    """
    Association table between Tracks and Service Patterns
    Represents which Tracks are used by which Service Patterns in sequence
    """

    __tablename__ = "transmodel_servicepattern_tracks"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, init=False, autoincrement=True
    )
    sequence_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tracks_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("transmodel_tracks.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
    )
    service_pattern_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "transmodel_servicepattern.id", deferrable=True, initially="DEFERRED"
        ),
        nullable=False,
    )
