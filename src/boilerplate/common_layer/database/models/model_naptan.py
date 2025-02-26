"""
Naptan Models
SQLAlchemy Models
"""

from functools import cached_property
from typing import cast

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from shapely.geometry import Point
from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel


class NaptanAdminArea(BaseSQLModel):
    """Naptan Admin Area Table"""

    __tablename__ = "naptan_adminarea"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    traveline_region_id: Mapped[str] = mapped_column(String(255), nullable=False)
    atco_code: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    ui_lta_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class NaptanLocality(BaseSQLModel):
    """
    Naptan Locality Table
    Lists all localities with gazetteer_id being the primary key
    """

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

    @cached_property
    def shape(self) -> Point:
        """
        Returns the shapely geometry of the location.
        Cached to avoid repeated conversions of the same geometry.
        """
        return cast(Point, to_shape(self.location))

    def __repr__(self) -> str:
        """
        Custom representation that shows shape coordinates instead of WKBElement
        when the object is printed
        """
        try:
            attributes = []
            for key, value in self.__dict__.items():
                if not key.startswith("_"):  # Skip SQLAlchemy internal attributes
                    if key == "location":
                        shape = self.shape
                        value_str = f"({shape.x:.6f},{shape.y:.6f})"
                        attributes.append(f"{key}={value_str}")
                    elif key == "shape":
                        pass
                    else:
                        value_str = repr(value)
                        attributes.append(f"{key}={value_str}")

            return f"NaptanStopPoint({', '.join(attributes)})"
        except Exception:
            # Fall back to default representation if there's an error
            return super().__repr__()
