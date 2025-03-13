"""
Factories for Naptan Database Data
"""

from typing import Any

import factory
from common_layer.database.models.model_naptan import NaptanAdminArea, NaptanStopPoint
from factory.fuzzy import FuzzyChoice
from geoalchemy2.shape import from_shape
from shapely import Point

from src.timetables_etl.etl.app.helpers.types import StopsLookup


class NaptanStopPointFactory(factory.Factory):
    """
    Factory for Naptan Stop Point Data
    This data is usually queried from the database and the ETL does not add anything to it
    """

    class Meta:  # type: ignore
        model = NaptanStopPoint

    atco_code = factory.Sequence(lambda n: f"490014051VC_{n}")
    naptan_code = None
    common_name = factory.Sequence(lambda n: f"Test Stop {n}")
    street = None
    indicator = None
    location = factory.LazyFunction(lambda: from_shape(Point(-3.5, 50.7), srid=4326))
    admin_area_id = None
    locality_id = None
    stop_areas = factory.List([])
    bus_stop_type = None
    stop_type = None

    @classmethod
    def create_with_id(cls, id_number: int, **kwargs: Any) -> NaptanStopPoint:
        """Creates a revision with a specific ID"""
        stop_point: NaptanStopPoint = cls.create(**kwargs)
        stop_point.id = id_number
        return stop_point

    @classmethod
    def create_mapping(cls, stop_data: list[tuple[str, str]]) -> StopsLookup:
        """Creates NaptanStopPoint mapping from list of (atco_code, common_name) tuples"""
        return {
            atco: cls.create(atco_code=atco, common_name=name)
            for atco, name in stop_data
        }

    @classmethod
    def create_mapping_with_locations(
        cls,
        stop_data: list[tuple[str, str, tuple[float, float]]],
    ) -> StopsLookup:
        """
        Creates NaptanStopPoint mapping from list of (atco_code, common_name, (lat, lon)) tuples
        """
        return {
            atco: cls.create(
                atco_code=atco,
                common_name=name,
                location=from_shape(Point(lon, lat), srid=4326),
            )
            for atco, name, (lon, lat) in stop_data
        }


class NaptanAdminAreaFactory(factory.Factory):
    """
    Factory for creating NaptanAdmin instances using the repository pattern.
    """

    class Meta:  # type: ignore
        model = NaptanAdminArea

    name = FuzzyChoice(
        choices=[
            "Stockton-on-Tees",
            "West Dunbartonshire",
            "East Dunbartonshire",
            "Surrey",
            "Thurrock",
        ]
    )

    traveline_region_id = FuzzyChoice(
        choices=[
            "N",
            "NE",
            "E",
            "SE",
            "S",
            "SW",
            "W",
        ]
    )
    atco_code = factory.Sequence(lambda n: f"ATC00{n}")
    ui_lta_id = None
