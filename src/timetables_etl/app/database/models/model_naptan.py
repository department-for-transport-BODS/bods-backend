"""
Naptan Models
SQLAlchemy Models
"""

import logging
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .common import BaseSQLModel

logger = logging.getLogger(__name__)


class UILta(BaseSQLModel):
    """
    UI LTA (Local Transport Authority) Model
    Table: ui_lta
    """

    __tablename__ = "ui_lta"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Basic Fields
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True, kw_only=True)


class AdminArea(BaseSQLModel):
    """
    Admin Area Model
    Table: admin_areas
    """

    __tablename__ = "admin_areas"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Basic Fields
    name: Mapped[str] = mapped_column(String(255), nullable=False, kw_only=True)
    traveline_region_id: Mapped[str] = mapped_column(
        String(255), nullable=False, kw_only=True
    )
    atco_code: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, kw_only=True
    )

    # Foreign Keys
    ui_lta_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("ui_lta.id", ondelete="CASCADE"),
        nullable=True,
        default=None,
        kw_only=True,
    )


class District(BaseSQLModel):
    """
    District Model representing a geographic district
    Table: districts
    """

    __tablename__ = "districts"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Basic Fields
    name: Mapped[str] = mapped_column(String(255), nullable=False, kw_only=True)


class Locality(BaseSQLModel):
    """
    Locality Model representing a geographic area
    Table: localities
    """

    __tablename__ = "localities"

    # Primary Key - using gazetteer_id instead of auto-incrementing id
    gazetteer_id: Mapped[str] = mapped_column(
        String(8), primary_key=True, nullable=False, kw_only=True
    )

    # Basic Fields
    name: Mapped[str] = mapped_column(String(255), nullable=False, kw_only=True)
    easting: Mapped[int] = mapped_column(Integer, nullable=False, kw_only=True)
    northing: Mapped[int] = mapped_column(Integer, nullable=False, kw_only=True)

    # Foreign Keys
    district_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("districts.id", ondelete="SET NULL"), nullable=True, kw_only=True
    )
    admin_area_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("admin_areas.id", ondelete="SET NULL"), nullable=True, kw_only=True
    )


class StopPoint(BaseSQLModel):
    """
    StopPoint Model representing a public transport stop location
    """

    __tablename__ = "stop_points"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Basic Fields
    atco_code: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, kw_only=True
    )
    naptan_code: Mapped[Optional[str]] = mapped_column(
        String(12), nullable=True, kw_only=True
    )
    common_name: Mapped[str] = mapped_column(String(255), nullable=False, kw_only=True)
    street: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, kw_only=True
    )
    indicator: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, kw_only=True
    )
    location: Mapped[str] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=False, kw_only=True
    )

    # Foreign Keys
    locality_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("localities.id", ondelete="SET NULL"), nullable=True, kw_only=True
    )
    admin_area_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("admin_areas.id", ondelete="SET NULL"), nullable=True, kw_only=True
    )

    # Array Field
    stop_areas: Mapped[list[str]] = mapped_column(
        ARRAY(String(255)), default=list, kw_only=True
    )

    # Type Fields
    stop_type: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, kw_only=True
    )
    bus_stop_type: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, kw_only=True
    )
