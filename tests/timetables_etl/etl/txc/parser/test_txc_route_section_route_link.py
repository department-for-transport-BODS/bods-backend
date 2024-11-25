"""
TXC Stoppoint XML to Pydantic Test
"""

from datetime import datetime, timezone

import pytest
from lxml import etree

from timetables_etl.etl.app.txc.models import TXCLocation, TXCRouteLink, TXCTrack
from timetables_etl.etl.app.txc.models.txc_route import TXCMapping
from timetables_etl.etl.app.txc.parser.route_sections import (
    parse_route_link,
    parse_route_links,
    parse_track,
)


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        (
            """
        <RouteLink>
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
        </RouteLink>
        """,
            TXCTrack(
                Mapping=TXCMapping(
                    Location=[
                        TXCLocation(
                            id="loc1", Longitude="-0.1234567", Latitude="51.9876543"
                        ),
                        TXCLocation(id="loc2", Longitude="0.0", Latitude="0.0"),
                    ]
                )
            ),
        ),
        (
            """
        <RouteLink>
            <Track>
                <Mapping>
                    <Location>
                        <Longitude>-0.1234567</Longitude>
                        <Latitude>51.9876543</Latitude>
                    </Location>
                </Mapping>
            </Track>
        </RouteLink>
        """,
            None,
        ),
        (
            """
        <RouteLink>
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
        </RouteLink>
        """,
            TXCTrack(
                Mapping=TXCMapping(
                    Location=[
                        TXCLocation(
                            id="loc1", Longitude="-0.1234567", Latitude="51.9876543"
                        ),
                    ]
                )
            ),
        ),
        (
            """
        <RouteLink>
            <InvalidElement>
                <Mapping>
                    <Location id="loc1">
                        <Longitude>-0.1234567</Longitude>
                        <Latitude>51.9876543</Latitude>
                    </Location>
                </Mapping>
            </InvalidElement>
        </RouteLink>
        """,
            None,
        ),
        (
            """
        <RouteLink></RouteLink>
        """,
            None,
        ),
    ],
    ids=[
        "Valid Track",
        "Missing Location ID",
        "Mixed Valid and Invalid Locations",
        "Invalid Track Element",
        "No Track Element",
    ],
)
def test_parse_track(xml_string, expected):
    """
    Test the parsing of TXCTrack from XML.
    """
    root = etree.fromstring(xml_string)
    assert parse_track(root) == expected


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        (
            """
        <RouteLink id="RL1"
                CreationDateTime="2023-05-15T10:30:00+00:00"
                ModificationDateTime="2023-05-16T12:45:00+00:00"
                Modification="revise"
                RevisionNumber="5">
            <From>
                <StopPointRef>2400A039650A</StopPointRef>
            </From>
            <To>
                <StopPointRef>2400A050290A</StopPointRef>
            </To>
            <Distance>1000</Distance>
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
        </RouteLink>
        """,
            TXCRouteLink(
                id="RL1",
                From="2400A039650A",
                To="2400A050290A",
                CreationDateTime=datetime(2023, 5, 15, 10, 30, tzinfo=timezone.utc),
                ModificationDateTime=datetime(2023, 5, 16, 12, 45, tzinfo=timezone.utc),
                Modification="revise",
                RevisionNumber=5,
                Distance=1000,
                Track=TXCTrack(
                    Mapping=TXCMapping(
                        Location=[
                            TXCLocation(
                                id="loc1", Longitude="-0.1234567", Latitude="51.9876543"
                            ),
                            TXCLocation(id="loc2", Longitude="0.0", Latitude="0.0"),
                        ]
                    )
                ),
            ),
        ),
        (
            """
        <RouteLink>
            <From>
                <StopPointRef>2400A039650A</StopPointRef>
            </From>
            <To>
                <StopPointRef>2400A050290A</StopPointRef>
            </To>
        </RouteLink>
        """,
            None,
        ),
        (
            """
        <RouteLink id="RL2">
            <To>
                <StopPointRef>2400A050290A</StopPointRef>
            </To>
        </RouteLink>
        """,
            None,
        ),
        (
            """
        <RouteLink id="RL3">
            <From>
                <StopPointRef>2400A039650A</StopPointRef>
            </From>
        </RouteLink>
        """,
            None,
        ),
        (
            """
        <RouteLink id="RL4">
            <From>
                <StopPointRef>2400A039650A</StopPointRef>
            </From>
            <To>
                <StopPointRef>2400A050290A</StopPointRef>
            </To>
            <Track>
                <InvalidElement>
                    <Mapping>
                        <Location id="loc1">
                            <Longitude>-0.1234567</Longitude>
                            <Latitude>51.9876543</Latitude>
                        </Location>
                    </Mapping>
                </InvalidElement>
            </Track>
        </RouteLink>
        """,
            TXCRouteLink(
                id="RL4",
                From="2400A039650A",
                To="2400A050290A",
                CreationDateTime=None,
                ModificationDateTime=None,
                Modification=None,
                RevisionNumber=None,
                Distance=None,
                Track=None,
            ),
        ),
    ],
    ids=[
        "Valid RouteLink",
        "Missing ID",
        "Missing From StopPointRef",
        "Missing To StopPointRef",
        "Invalid Track Element",
    ],
)
def test_parse_route_link(xml_string, expected):
    """
    Test the parsing of TXCRouteLink from XML.
    """
    root = etree.fromstring(xml_string)
    assert parse_route_link(root, True) == expected


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        (
            """
        <RouteSection>
            <RouteLink id="RL1"
                       CreationDateTime="2023-05-15T10:30:00+00:00"
                       ModificationDateTime="2023-05-16T12:45:00+00:00"
                       Modification="revise"
                       RevisionNumber="5">
                <From>
                    <StopPointRef>2400A039650A</StopPointRef>
                </From>
                <To>
                    <StopPointRef>2400A050290A</StopPointRef>
                </To>
                <Distance>1000</Distance>
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
            </RouteLink>
        </RouteSection>
        """,
            [
                TXCRouteLink(
                    id="RL1",
                    From="2400A039650A",
                    To="2400A050290A",
                    CreationDateTime=datetime(2023, 5, 15, 10, 30, tzinfo=timezone.utc),
                    ModificationDateTime=datetime(
                        2023, 5, 16, 12, 45, tzinfo=timezone.utc
                    ),
                    Modification="revise",
                    RevisionNumber=5,
                    Distance=1000,
                    Track=TXCTrack(
                        Mapping=TXCMapping(
                            Location=[
                                TXCLocation(
                                    id="loc1",
                                    Longitude="-0.1234567",
                                    Latitude="51.9876543",
                                ),
                                TXCLocation(id="loc2", Longitude="0.0", Latitude="0.0"),
                            ]
                        )
                    ),
                )
            ],
        ),
        (
            """
        <RouteSection>
            <RouteLink id="RL1">
                <From>
                    <StopPointRef>2400A039650A</StopPointRef>
                </From>
                <To>
                    <StopPointRef>2400A050290A</StopPointRef>
                </To>
            </RouteLink>
            <RouteLink id="RL2"
                       CreationDateTime="2023-05-17T09:00:00+00:00"
                       ModificationDateTime="2023-05-18T14:30:00+00:00"
                       Modification="new"
                       RevisionNumber="1">
                <From>
                    <StopPointRef>2400A050290A</StopPointRef>
                </From>
                <To>
                    <StopPointRef>240096719</StopPointRef>
                </To>
                <Distance>800</Distance>
            </RouteLink>
        </RouteSection>
        """,
            [
                TXCRouteLink(
                    id="RL1",
                    From="2400A039650A",
                    To="2400A050290A",
                    CreationDateTime=None,
                    ModificationDateTime=None,
                    Modification=None,
                    RevisionNumber=None,
                    Distance=None,
                    Track=None,
                ),
                TXCRouteLink(
                    id="RL2",
                    From="2400A050290A",
                    To="240096719",
                    CreationDateTime=datetime(2023, 5, 17, 9, 0, tzinfo=timezone.utc),
                    ModificationDateTime=datetime(
                        2023, 5, 18, 14, 30, tzinfo=timezone.utc
                    ),
                    Modification="new",
                    RevisionNumber=1,
                    Distance=800,
                    Track=None,
                ),
            ],
        ),
        (
            """
        <RouteSection>
            <InvalidElement />
        </RouteSection>
        """,
            [],
        ),
        (
            """
        <InvalidTopLevel />
        """,
            [],
        ),
    ],
    ids=[
        "Single Valid RouteLink",
        "Multiple RouteLinks",
        "Invalid RouteLink Element",
        "Invalid Top-level Element",
    ],
)
def test_parse_route_links(xml_string, expected):
    """
    Test the parsing of TXCRouteLink list from XML.
    """
    root = etree.fromstring(xml_string)
    assert parse_route_links(root, True) == expected
