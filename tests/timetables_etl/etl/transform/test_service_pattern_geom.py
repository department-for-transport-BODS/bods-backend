import pytest
from common_layer.database.models import NaptanStopPoint
from common_layer.xml.txc.models import LocationStructure
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry.linestring import LineString
from shapely.geometry.point import Point

from tests.factories.database import NaptanStopPointFactory
from timetables_etl.etl.app.helpers.types import FlexibleZoneLookup
from timetables_etl.etl.app.transform.service_pattern_geom import (
    generate_service_pattern_geometry_from_list,
)


@pytest.mark.parametrize(
    "stop_points,flexible_zone_lookup,expected_line_string",
    [
        pytest.param(
            [
                NaptanStopPointFactory.create(
                    atco_code="030058940001",
                    location=from_shape(Point(-1.123, 51.504), srid=4326),
                ),
                NaptanStopPointFactory.create(
                    atco_code="030058930001",
                    location=from_shape(Point(-1.141, 51.482), srid=4326),
                ),
            ],
            {
                "030058940001": [
                    LocationStructure(Easting="461257", Northing="178495"),
                    LocationStructure(Easting="460801", Northing="178590"),
                ]
            },
            LineString(
                [
                    Point(-1.123, 51.504),
                    Point(-1.119, 51.502),
                    Point(-1.125, 51.503),
                    Point(-1.141, 51.482),
                ],
            ),
            id="Stops with flexible zones",
        ),
        pytest.param(
            [
                NaptanStopPointFactory.create(
                    atco_code="030058940001",
                    location=from_shape(Point(-1.123, 51.504), srid=4326),
                ),
                NaptanStopPointFactory.create(
                    atco_code="030058930001",
                    location=from_shape(Point(-1.141, 51.482), srid=4326),
                ),
            ],
            None,
            LineString(
                [
                    Point(-1.123, 51.504),
                    Point(-1.141, 51.482),
                ],
            ),
            id="No flexible zones",
        ),
    ],
)
def test_generate_service_pattern_geometry_from_list(
    flexible_zone_lookup: FlexibleZoneLookup | None,
    stop_points: list[NaptanStopPoint],
    expected_line_string: LineString,
):
    result = generate_service_pattern_geometry_from_list(
        stop_points, flexible_zone_lookup
    )
    assert result is not None
    assert to_shape(result).equals_exact(expected_line_string, tolerance=1e-3)
