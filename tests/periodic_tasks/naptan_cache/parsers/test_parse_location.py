"""
Test Parsing Location XML
"""

import numpy as np
import pytest
from lxml import etree

from periodic_tasks.naptan_cache.app.data_loader.parsers.parser_location import (
    parse_location,
)
from tests.periodic_tasks.naptan_cache.parsers.common import (
    create_stop_point,
    parse_xml_to_stop_point,
)


def assert_location_data_approx_equal(
    result: dict[str, str | None] | None, expected: dict[str, str | None] | None
) -> None:
    """
    Compare location data with special handling for latitude and longitude.
    """
    # If both are None, that's fine
    if result is None and expected is None:
        return

    # If expected is None but result is not, that's a failure
    assert result is not None, "Result is not None when expected is None"
    assert expected is not None, "Result is not None when expected is None"
    # Check non-float keys exactly
    non_float_keys = [
        key for key in result.keys() if key not in ["Longitude", "Latitude"]
    ]
    for key in non_float_keys:
        assert result[key] == expected[key], f"Mismatch in {key}"

    # Handle float comparison with None check
    for key in ["Longitude", "Latitude"]:
        result_value = result.get(key)
        expected_value = expected.get(key)

        # If either value is None, they must both be None
        if result_value is None or expected_value is None:
            assert result_value == expected_value, f"Mismatch in {key}"
            continue

        # Convert to floats and compare
        np.testing.assert_almost_equal(
            float(result_value), float(expected_value), decimal=10
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
                            <Longitude>-2.585789031283037</Longitude>
                            <Latitude>51.449021016827182</Latitude>
                            <Easting>359389</Easting>
                            <Northing>172389</Northing>
                        </Translation>
                    </Location>
                </Place>
            """
            ),
            {
                "Longitude": "-2.585789031283037",
                "Latitude": "51.449021016827182",
                "Easting": "359389",
                "Northing": "172389",
            },
            id="Bristol City Centre - Complete Location Data",
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
                "Longitude": "-2.585789031283037",
                "Latitude": "51.449021016827182",
                "Easting": "359389",
                "Northing": "172389",
            },
            id="Bristol City Centre - Only Easting Northing",
        ),
        pytest.param(
            create_stop_point(
                """
                <Place>
                    <Location>
                        <Translation>
                            <Easting>383187</Easting>
                            <Northing>398952</Northing>
                        </Translation>
                    </Location>
                </Place>
            """
            ),
            {
                "Longitude": "-2.254849141174204",
                "Latitude": "53.487009628400806",
                "Easting": "383187",
                "Northing": "398952",
            },
            id="Manchester City Centre - Only Easting Northing",
        ),
        pytest.param(
            create_stop_point(
                """
                <Place>
                    <Location>
                        <Translation>
                            <Easting>325225</Easting>
                            <Northing>672254</Northing>
                        </Translation>
                    </Location>
                </Place>
            """
            ),
            {
                "Longitude": "-3.198577617802602",
                "Latitude": "55.937500981811695",
                "Easting": "325225",
                "Northing": "672254",
            },
            id="Edinburgh City Centre - Only Easting Northing",
        ),
        pytest.param(
            create_stop_point(
                """
                <Place>
                    <Location>
                        <Translation>
                            <Easting>317929</Easting>
                            <Northing>175958</Northing>
                        </Translation>
                    </Location>
                </Place>
            """
            ),
            {
                "Longitude": "-3.183132532733615",
                "Latitude": "51.476605537318832",
                "Easting": "317929",
                "Northing": "175958",
            },
            id="Cardiff City Centre - Only Easting Northing",
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
            {
                "Easting": "359389",
                "Latitude": "51.44902",
                "Longitude": "-2.58579",
                "Northing": "172389",
            },
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
    assert_location_data_approx_equal(result, expected)
