"""
Tables prefixed data_quality_
SQLAlchemy Models
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, List

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Interval,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql import text

from .common import BaseSQLModel

if TYPE_CHECKING:
    from .model_organisation import OrganisationDatasetrevision
    from .model_transmodel import TransmodelService, TransmodelVehicleJourney


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
        ForeignKey("organisation_datasetrevision.id", ondelete="CASCADE"),
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

    # Relationships
    revision: Mapped["OrganisationDatasetrevision"] = relationship(
        "OrganisationDatasetrevision",
        back_populates="report",
        default=None,
        kw_only=True,
    )

    # Many-to-many relationship with Service
    services: Mapped[list["TransmodelService"]] = relationship(
        "Service",
        secondary="service_dataquality_report",
        back_populates="reports",
        default_factory=list,
        kw_only=True,
    )

    # Constraints and ordering
    __table_args__ = (
        CheckConstraint(
            "score >= 0.0 AND score <= 1.0", name="dq_score_must_be_between_0_and_1"
        ),
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
        ForeignKey("service_pattern.id", ondelete="CASCADE"),
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

    # Relationships
    service_pattern: Mapped["DataQualityServicepattern"] = relationship(
        "DataQualityServicepattern",
        back_populates="service_pattern_stops",
        default=None,
        kw_only=True,
    )

    stop: Mapped["DataQualityStopPoint"] = relationship(
        "DataQualityStopPoint",
        back_populates="service_pattern_stops",
        default=None,
        kw_only=True,
    )

    # Added relationship for TimingPatternStop
    timings: Mapped[list["DataQualityTimingPatternStop"]] = relationship(
        "DataQualityTimingPatternStop",
        back_populates="service_pattern_stop",
        default_factory=list,
        kw_only=True,
    )
    timing_pattern: Mapped["DataQualityTimingPattern"] = relationship(
        "DataQualityTimingPattern",
        back_populates="service_pattern_stops",
        default=None,
        kw_only=True,
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
        ForeignKey("service_pattern.id", ondelete="CASCADE"),
        nullable=False,
        kw_only=True,
        doc="Reference to the associated service pattern",
    )

    service_link_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("service_link.id", ondelete="PROTECT"),
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

    # Relationships
    service_pattern: Mapped["DataQualityServicepattern"] = relationship(
        "ServicePattern",
        back_populates="service_pattern_service_links",
        default=None,
        kw_only=True,
    )

    service_link: Mapped["DataQualityServiceLink"] = relationship(
        "ServiceLink",
        back_populates="service_pattern_service_links",
        default=None,
        kw_only=True,
    )

    # Unique constraint equivalent to Django's unique_together
    __table_args__ = (
        UniqueConstraint(
            "service_pattern_id",
            "service_link_id",
            "position",
            name="uix_service_pattern_service_link_unique",
        ),
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
        ForeignKey("stop_point.id", ondelete="PROTECT"),
        nullable=False,
        kw_only=True,
        doc="Reference to the origin stop point",
    )

    to_stop_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("stop_point.id", ondelete="PROTECT"),
        nullable=False,
        kw_only=True,
        doc="Reference to the destination stop point",
    )

    # Relationships
    from_stop: Mapped["DataQualityStopPoint"] = relationship(
        "DataQualityStopPoint",
        foreign_keys=[from_stop_id],
        back_populates="from_service_links",
        default=None,
        kw_only=True,
    )

    to_stop: Mapped["DataQualityStopPoint"] = relationship(
        "DataQualityStopPoint",
        foreign_keys=[to_stop_id],
        back_populates="to_service_links",
        default=None,
        kw_only=True,
    )

    # Relationships for the through tables
    service_pattern_service_links: Mapped[
        List["DataQualityServicePatternServiceLink"]
    ] = relationship(
        "DataQualityServicePatternServiceLink",
        back_populates="service_link",
        default_factory=list,
        kw_only=True,
    )

    # Unique constraint
    __table_args__ = (
        UniqueConstraint("from_stop_id", "to_stop_id", name="uix_service_link_stops"),
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
        ForeignKey("service.id", ondelete="CASCADE"),
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

    # Relationships
    service: Mapped["TransmodelService"] = relationship(
        "Service", back_populates="service_patterns", default=None, kw_only=True
    )

    timing_patterns: Mapped[list["DataQualityTimingPattern"]] = relationship(
        "DataQualityTimingPattern",
        back_populates="service_pattern",
        default_factory=list,
        kw_only=True,
    )

    service_pattern_stops: Mapped[list["DataQualityServicePatternStop"]] = relationship(
        "DataQualityServicePatternStop",
        back_populates="service_pattern",
        default_factory=list,
        kw_only=True,
    )

    service_pattern_service_links: Mapped[
        list["DataQualityServicePatternServiceLink"]
    ] = relationship(
        "ServicePatternServiceLink",
        back_populates="service_pattern",
        default_factory=list,
        kw_only=True,
    )

    # Through relationships
    stops: Mapped[list["DataQualityStopPoint"]] = relationship(
        "DataQualityStopPoint",
        secondary="service_pattern_stop",
        back_populates="service_patterns",
        default_factory=list,
        kw_only=True,
    )

    service_links: Mapped[list["DataQualityServiceLink"]] = relationship(
        "DataQualityServiceLink",
        secondary="service_pattern_service_link",
        back_populates="service_patterns",
        default_factory=list,
        kw_only=True,
    )

    timing_pattern_stops: Mapped[list["DataQualityTimingPatternStop"]] = relationship(
        "DataQualityTimingPatternStop",
        back_populates="service_pattern",
        default_factory=list,
        kw_only=True,
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
        ForeignKey("service_pattern.id", ondelete="CASCADE"),
        nullable=False,
        kw_only=True,
        doc="Reference to the associated service pattern",
    )

    # Relationships
    service_pattern: Mapped["DataQualityServicepattern"] = relationship(
        "DataQualityServicepattern",
        back_populates="timing_patterns",
        default=None,
        kw_only=True,
    )

    # Reverse relationship to VehicleJourney
    vehicle_journeys: Mapped[list["TransmodelVehicleJourney"]] = relationship(
        "TransmodelVehicleJourney",
        back_populates="timing_pattern",
        default_factory=list,
        kw_only=True,
    )
    timing_pattern_stops: Mapped[list["DataQualityTimingPatternStop"]] = relationship(
        "DataQualityTimingPatternStop",
        back_populates="timing_pattern",
        default_factory=list,
        kw_only=True,
    )


class DataQualityTimingPatternStop(BaseSQLModel):
    __tablename__ = "data_quality_timingpatternstop"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    timing_pattern_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("timing_pattern.id", ondelete="CASCADE"),
        nullable=False,
        kw_only=True,
    )

    service_pattern_stop_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("service_pattern_stop.id", ondelete="CASCADE"),
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

    # Relationships
    timing_pattern: Mapped["DataQualityTimingPattern"] = relationship(
        "DataQualityTimingPattern",
        back_populates="timing_pattern_stops",
        default=None,
        kw_only=True,
    )

    service_pattern_stop: Mapped["DataQualityServicePatternStop"] = relationship(
        "DataQualityServicePatternStop",
        back_populates="timings",
        default=None,
        kw_only=True,
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

    # Relationships for the reverse foreign keys
    from_service_links: Mapped[list["DataQualityServiceLink"]] = relationship(
        "DataQualityServiceLink",
        foreign_keys="[ServiceLink.from_stop_id]",
        back_populates="from_stop",
        default_factory=list,
        kw_only=True,
    )

    to_service_links: Mapped[list["DataQualityServiceLink"]] = relationship(
        "DataQualityServiceLink",
        foreign_keys="[ServiceLink.to_stop_id]",
        back_populates="to_stop",
        default_factory=list,
        kw_only=True,
    )

    service_pattern_stops: Mapped[list["DataQualityServicePatternStop"]] = relationship(
        "ServicePatternStop", back_populates="stop", default_factory=list, kw_only=True
    )

    __table_args__ = (
        UniqueConstraint(
            "ito_id", "atco_code", "is_provisional", name="uix_stop_point_unique"
        ),
    )
