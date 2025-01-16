"""
Test Parsing Location XML
"""

import pytest
from lxml import etree

from periodic_tasks.naptan_cache.app.data_loader.parsers.parser_location import (
    parse_location,
)
from tests.periodic_tasks.naptan_cache.parsers.common import (
    create_stop_point,
    parse_xml_to_stop_point,
)


@pytest.mark.parametrize(
    ("xml_input", "expected"),
    [
        pytest.param(
            create_stop_point(
                """
                <Place>
                    <Location>
                        <Translation>
                            <Longitude>-2.58579</Longitude>
                            <Latitude>51.44902</Latitude>
                            <Easting>359389</Easting>
                            <Northing>172389</Northing>
                        </Translation>
                    </Location>
                </Place>
            """
            ),
            {
                "Longitude": "-2.58579",
                "Latitude": "51.44902",
                "Easting": "359389",
                "Northing": "172389",
            },
            id="Complete Location Data",
        ),
        pytest.param(
            create_stop_point(
                """
                <Place>
                    <Location>
                        <Translation>
                            <Easting>359389</Easting>
                            <Northing>172389</Northing>
                        </Translation>
                    </Location>
                </Place>
            """
            ),
            {
                "Longitude": None,
                "Latitude": None,
                "Easting": "359389",
                "Northing": "172389",
            },
            id="Only Easting Northing",
        ),
        pytest.param(
            create_stop_point(
                """
                <Place>
                    <Location>
                        <Translation>
                            <Longitude>-2.58579</Longitude>
                            <Latitude>51.44902</Latitude>
                        </Translation>
                    </Location>
                </Place>
            """
            ),
            None,
            id="No Easting Northing",
        ),
        pytest.param(create_stop_point("<Place></Place>"), None, id="NoLocationData"),
        pytest.param(create_stop_point(""), None, id="EmptyStopPoint"),
    ],
)
def test_parse_location(xml_input: str, expected: dict[str, str | None] | None) -> None:
    """
    Test parse_location function with various input scenarios.

    """
    stop_point: etree._Element = parse_xml_to_stop_point(xml_input)
    result: dict[str, str | None] | None = parse_location(stop_point)
    assert result == expected
