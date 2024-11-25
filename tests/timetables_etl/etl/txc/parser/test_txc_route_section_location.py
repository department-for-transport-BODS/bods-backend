"""
TXC Route Section Location XML to Pydantic Test
"""

import pytest
from lxml import etree

from timetables_etl.etl.app.txc.models.txc_route import TXCLocation
from timetables_etl.etl.app.txc.parser.route_sections import (
    parse_location,
    parse_locations,
)


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        (
            """
        <Location id="loc1">
            <Longitude>-0.1234567</Longitude>
            <Latitude>51.9876543</Latitude>
        </Location>
        """,
            TXCLocation(id="loc1", Longitude="-0.1234567", Latitude="51.9876543"),
        ),
        (
            """
        <Location id="loc2">
            <Longitude>0.0</Longitude>
            <Latitude>0.0</Latitude>
        </Location>
        """,
            TXCLocation(id="loc2", Longitude="0.0", Latitude="0.0"),
        ),
        (
            """
        <Location>
            <Longitude>-0.1234567</Longitude>
            <Latitude>51.9876543</Latitude>
        </Location>
        """,
            None,
        ),
        (
            """
        <Location id="loc3">
            <Latitude>51.9876543</Latitude>
        </Location>
        """,
            None,
        ),
        (
            """
        <Location id="loc4">
            <Longitude>-0.1234567</Longitude>
        </Location>
        """,
            None,
        ),
        (
            """
        <InvalidElement>
            <Longitude>-0.1234567</Longitude>
            <Latitude>51.9876543</Latitude>
        </InvalidElement>
        """,
            None,
        ),
    ],
    ids=[
        "Valid Location",
        "Valid Location with 0 Coordinates",
        "Missing Location ID",
        "Missing Longitude",
        "Missing Latitude",
        "Invalid Top-level Element",
    ],
)
def test_parse_location(xml_string, expected):
    """
    Test the parsing of TXCLocation from XML.
    """
    root = etree.fromstring(xml_string)
    assert parse_location(root) == expected


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        (
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
        ),
        (
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
        ),
        (
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
        ),
        (
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
        ),
        (
            """
        <Track></Track>
        """,
            None,
        ),
    ],
    ids=[
        "Multiple Valid Locations",
        "Missing Location ID",
        "Mixed Valid and Invalid Locations",
        "Invalid Top-level Element",
        "No Locations",
    ],
)
def test_parse_locations(xml_string, expected):
    """
    Test the parsing of TXCLocation list from XML.
    """
    root = etree.fromstring(xml_string)
    assert parse_locations(root) == expected
