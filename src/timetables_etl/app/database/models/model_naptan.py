"""
Naptan Models
SQLAlchemy Models
"""

import logging

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel

logger = logging.getLogger(__name__)


class NaptanAdminArea(BaseSQLModel):
    """Naptan Admin Area Table"""

    __tablename__ = "naptan_adminarea"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    traveline_region_id: Mapped[str] = mapped_column(String(255), nullable=False)
    atco_code: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    ui_lta_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class NaptanLocality(BaseSQLModel):
    """Naptan Locality Table"""

    __tablename__ = "naptan_locality"

    gazetteer_id: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    easting: Mapped[int] = mapped_column(Integer, nullable=False)
    northing: Mapped[int] = mapped_column(Integer, nullable=False)
    admin_area_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    district_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class NaptanStopPoint(BaseSQLModel):
    """Naptan Stop Point Table"""

    __tablename__ = "naptan_stoppoint"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    atco_code: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    naptan_code: Mapped[str | None] = mapped_column(String(12), nullable=True)
    common_name: Mapped[str] = mapped_column(String(255), nullable=False)
    street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    indicator: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[WKBElement] = mapped_column(
        Geometry("POINT", 4326), nullable=False
    )
    admin_area_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    locality_id: Mapped[str | None] = mapped_column(String(8), nullable=True)
    stop_areas: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    bus_stop_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stop_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
