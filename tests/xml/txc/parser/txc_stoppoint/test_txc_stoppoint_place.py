"""
Test Parsing Place
"""

import pytest
from common_layer.xml.txc.models import LocationStructure, PlaceStructure
from common_layer.xml.txc.parser.stop_points import (
    parse_location_structure,
    parse_place_structure,
)
from lxml.etree import fromstring


@pytest.mark.parametrize(
    "location_xml_str, expected_result",
    [
        pytest.param(
            """
            <Location>
                <Translation>
                    <Longitude>-6.253318</Longitude>
                    <Latitude>53.347398</Latitude>
                    <Easting>117018</Easting>
                    <Northing>391827</Northing>
                </Translation>
            </Location>
            """,
            LocationStructure(
                Longitude="-6.253318",
                Latitude="53.347398",
                Easting="117018",
                Northing="391827",
            ),
            id="Valid Location Structure",
        ),
        pytest.param(
            """
            <Location>
                <Translation>
                    <Longitude>-6.253318</Longitude>
                    <Latitude>53.347398</Latitude>
                </Translation>
            </Location>
            """,
            LocationStructure(
                Longitude="-6.253318",
                Latitude="53.347398",
                Easting=None,
                Northing=None,
            ),
            id="Missing Easting and Northing",
        ),
    ],
)
def test_parse_location_structure(
    location_xml_str: str, expected_result: LocationStructure | None
):
    """
    Testing location structure parsing
    """
    location_xml = fromstring(location_xml_str)
    assert parse_location_structure(location_xml) == expected_result


@pytest.mark.parametrize(
    "place_xml_str, expected_result",
    [
        pytest.param(
            """
            <Place>
                <NptgLocalityRef>N0075743</NptgLocalityRef>
                <LocalityName>Dublin - George's Quay (Tara St Station)</LocalityName>
                <Location>
                    <Translation>
                        <Longitude>-6.253318</Longitude>
                        <Latitude>53.347398</Latitude>
                        <Easting>117018</Easting>
                        <Northing>391827</Northing>
                    </Translation>
                </Location>
            </Place>
            """,
            PlaceStructure(
                NptgLocalityRef="N0075743",
                LocalityName="Dublin - George's Quay (Tara St Station)",
                Location=LocationStructure(
                    Longitude="-6.253318",
                    Latitude="53.347398",
                    Easting="117018",
                    Northing="391827",
                ),
            ),
            id="Valid Place Structure",
        ),
        pytest.param(
            """
            <Place>
                <LocalityName>Dublin - George's Quay (Tara St Station)</LocalityName>
                <Location>
                    <Translation>                
                        <Longitude>-6.253318</Longitude>
                        <Latitude>53.347398</Latitude>
                        <Easting>117018</Easting>
                        <Northing>391827</Northing>
                    </Translation>
                </Location>
            </Place>
            """,
            None,
            id="Missing NptgLocalityRef",
        ),
        pytest.param(
            """
            <Place>
                <NptgLocalityRef>N0075743</NptgLocalityRef>
                <LocalityName>Dublin - George's Quay (Tara St Station)</LocalityName>
            </Place>
            """,
            None,
            id="Missing Location",
        ),
    ],
)
def test_parse_place_structure(
    place_xml_str: str, expected_result: PlaceStructure | None
):
    """
    Parsing entire place structure
    """
    place_xml = fromstring(place_xml_str)
    assert parse_place_structure(place_xml) == expected_result
