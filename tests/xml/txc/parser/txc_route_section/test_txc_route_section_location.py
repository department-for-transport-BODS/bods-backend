"""
TXC Route Section Location XML to Pydantic Test
"""

import pytest
from common_layer.xml.txc.models import TXCLocation
from common_layer.xml.txc.parser.route_sections import parse_location, parse_locations
from lxml import etree


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        pytest.param(
            """
        <Location id="loc1">
            <Longitude>-0.1234567</Longitude>
            <Latitude>51.9876543</Latitude>
        </Location>
        """,
            TXCLocation(id="loc1", Longitude="-0.1234567", Latitude="51.9876543"),
            id="Valid Location",
        ),
        pytest.param(
            """
        <Location id="loc2">
            <Longitude>0.0</Longitude>
            <Latitude>0.0</Latitude>
        </Location>
        """,
            TXCLocation(id="loc2", Longitude="0.0", Latitude="0.0"),
            id="Valid Location with 0 Coordinates",
        ),
        pytest.param(
            """
        <Location>
            <Longitude>-0.1234567</Longitude>
            <Latitude>51.9876543</Latitude>
        </Location>
        """,
            None,
            id="Missing Location ID",
        ),
        pytest.param(
            """
        <Location id="loc3">
            <Latitude>51.9876543</Latitude>
        </Location>
        """,
            None,
            id="Missing Longitude",
        ),
        pytest.param(
            """
        <Location id="loc4">
            <Longitude>-0.1234567</Longitude>
        </Location>
        """,
            None,
            id="Missing Latitude",
        ),
        pytest.param(
            """
        <InvalidElement>
            <Longitude>-0.1234567</Longitude>
            <Latitude>51.9876543</Latitude>
        </InvalidElement>
        """,
            None,
            id="Invalid Top-level Element",
        ),
    ],
)
def test_parse_location(xml_string: str, expected: TXCLocation | None) -> None:
    """
    Test the parsing of TXCLocation from XML.
    """
    root = etree.fromstring(xml_string)
    assert parse_location(root) == expected


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        pytest.param(
            """
        <Track>
            <Mapping>
                <Location id="loc1">
                    <Longitude>-0.1234567</Longitude>
                    <Latitude>51.9876543</Latitude>
                </Location>
                <Location id="loc2">
                    <Longitude>0.0</Longitude>
                    <Latitude>0.0</Latitude>
                </Location>
            </Mapping>
        </Track>
        """,
            [
                TXCLocation(id="loc1", Longitude="-0.1234567", Latitude="51.9876543"),
                TXCLocation(id="loc2", Longitude="0.0", Latitude="0.0"),
            ],
            id="Multiple Valid Locations",
        ),
        pytest.param(
            """
        <Track>
            <Mapping>
                <Location id="loc1">
                    <Easting>097910</Easting>
                    <Northing>960550</Northing>
                </Location>
                <Location id="loc2">
                    <Easting>097460</Easting>
                    <Northing>960340</Northing>
                </Location>
            </Mapping>
        </Track>
        """,
            [
                TXCLocation(
                    id="loc1",
                    Longitude="-7.177380811839908",
                    Latitude="58.42846940467045",
                ),
                TXCLocation(
                    id="loc2",
                    Longitude="-7.184777481473526",
                    Latitude="58.426280107812424",
                ),
            ],
            id="Multiple Valid Locations with Easting and Northing",
        ),
        pytest.param(
            """
        <Track>
            <Mapping>
                <Location>
                    <Longitude>-0.1234567</Longitude>
                    <Latitude>51.9876543</Latitude>
                </Location>
            </Mapping>
        </Track>
        """,
            [],
            id="Missing Location ID",
        ),
        pytest.param(
            """
        <Track>
            <Mapping>
                <Location id="loc1">
                    <Longitude>-0.1234567</Longitude>
                    <Latitude>51.9876543</Latitude>
                </Location>
                <InvalidElement>
                    <Longitude>0.0</Longitude>
                    <Latitude>0.0</Latitude>
                </InvalidElement>
            </Mapping>
        </Track>
        """,
            [TXCLocation(id="loc1", Longitude="-0.1234567", Latitude="51.9876543")],
            id="Mixed Valid and Invalid Locations",
        ),
        pytest.param(
            """
        <Track>
        <Mapping>
            <Location id="loc2">
            <Translation>
                <Easting>495966</Easting>
                <Northing>201754</Northing>
                <Longitude>-0.612551</Longitude>
                <Latitude>51.706335</Latitude>
            </Translation>
            </Location>
        </Mapping>
        </Track>
        """,
            [TXCLocation(id="loc2", Longitude="-0.612551", Latitude="51.706335")],
            id="Location with translation element",
        ),
        pytest.param(
            """
        <InvalidTopLevel>
            <Mapping>
                <Location id="loc1">
                    <Longitude>-0.1234567</Longitude>
                    <Latitude>51.9876543</Latitude>
                </Location>
            </Mapping>
        </InvalidTopLevel>
        """,
            None,
            id="Invalid Top-level Element",
        ),
        pytest.param(
            """
        <Track></Track>
        """,
            None,
            id="No Locations",
        ),
    ],
)
def test_parse_locations(xml_string: str, expected: list[TXCLocation] | None):
    """
    Test the parsing of TXCLocation list from XML.
    """
    root = etree.fromstring(xml_string)
    assert parse_locations(root) == expected
