"""
TXC Stoppoint XML to Pydantic Test
"""

from datetime import datetime, timezone

import pytest
from lxml import etree

from timetables_etl.etl.app.txc.models import RouteSection
from timetables_etl.etl.app.txc.models.txc_route import (
    TXCLocation,
    TXCMapping,
    TXCRouteLink,
    TXCTrack,
)
from timetables_etl.etl.app.txc.parser.route_sections import (
    parse_route_section,
    parse_route_sections,
)


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        pytest.param(
            """
        <RouteSection id="RS1"
                      CreationDateTime="2023-05-15T10:30:00+00:00"
                      ModificationDateTime="2023-05-16T12:45:00+00:00">
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
            RouteSection(
                id="RS1",
                CreationDateTime=datetime(2023, 5, 15, 10, 30, tzinfo=timezone.utc),
                ModificationDateTime=datetime(2023, 5, 16, 12, 45, tzinfo=timezone.utc),
                RouteLink=[
                    TXCRouteLink(
                        id="RL1",
                        From="2400A039650A",
                        To="2400A050290A",
                        CreationDateTime=datetime(
                            2023, 5, 15, 10, 30, tzinfo=timezone.utc
                        ),
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
                                    TXCLocation(
                                        id="loc2", Longitude="0.0", Latitude="0.0"
                                    ),
                                ]
                            )
                        ),
                    )
                ],
            ),
            id="Valid RouteSection",
        ),
        pytest.param(
            """
        <RouteSection id="RS2">
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
            RouteSection(
                id="RS2",
                CreationDateTime=None,
                ModificationDateTime=None,
                RouteLink=[
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
                        CreationDateTime=datetime(
                            2023, 5, 17, 9, 0, tzinfo=timezone.utc
                        ),
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
            id="Valid RouteSection with Multiple RouteLinks",
        ),
        pytest.param(
            """
        <InvalidTopLevel />
        """,
            None,
            id="Invalid Top-level Element",
        ),
    ],
)
def test_parse_route_section(xml_string: str, expected: RouteSection):
    """
    Test the parsing of RouteSection from XML.
    """
    root = etree.fromstring(xml_string)
    assert parse_route_section(root, True) == expected


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        pytest.param(
            """
        <TransXChange>
            <RouteSections>
                <RouteSection id="RS1">
                    <RouteLink id="RL1">
                        <From>
                            <StopPointRef>2400A039650A</StopPointRef>
                        </From>
                        <To>
                            <StopPointRef>2400A050290A</StopPointRef>
                        </To>
                    </RouteLink>
                </RouteSection>
            </RouteSections>
        </TransXChange>
        """,
            [
                RouteSection(
                    id="RS1",
                    RouteLink=[
                        TXCRouteLink(
                            id="RL1",
                            From="2400A039650A",
                            To="2400A050290A",
                        )
                    ],
                )
            ],
            id="Single RouteSection with Single RouteLink",
        ),
        pytest.param(
            """
        <TransXChange>
            <RouteSections>
                <RouteSection id="RS1">
                    <RouteLink id="RL1">
                        <From>
                            <StopPointRef>2400A039650A</StopPointRef>
                        </From>
                        <To>
                            <StopPointRef>2400A050290A</StopPointRef>
                        </To>
                    </RouteLink>
                    <RouteLink id="RL2">
                        <From>
                            <StopPointRef>2400A050290A</StopPointRef>
                        </From>
                        <To>
                            <StopPointRef>240096719</StopPointRef>
                        </To>
                    </RouteLink>
                </RouteSection>
            </RouteSections>
        </TransXChange>
        """,
            [
                RouteSection(
                    id="RS1",
                    RouteLink=[
                        TXCRouteLink(
                            id="RL1",
                            From="2400A039650A",
                            To="2400A050290A",
                        ),
                        TXCRouteLink(
                            id="RL2",
                            From="2400A050290A",
                            To="240096719",
                        ),
                    ],
                )
            ],
            id="Single RouteSection with Multiple RouteLinks",
        ),
        pytest.param(
            """
        <TransXChange>
            <RouteSections>
                <RouteSection id="RS1">
                    <RouteLink id="RL1">
                        <From>
                            <StopPointRef>2400A039650A</StopPointRef>
                        </From>
                        <To>
                            <StopPointRef>2400A050290A</StopPointRef>
                        </To>
                    </RouteLink>
                </RouteSection>
                <RouteSection id="RS2">
                    <RouteLink id="RL2">
                        <From>
                            <StopPointRef>2400A050290A</StopPointRef>
                        </From>
                        <To>
                            <StopPointRef>240096719</StopPointRef>
                        </To>
                    </RouteLink>
                </RouteSection>
            </RouteSections>
        </TransXChange>
        """,
            [
                RouteSection(
                    id="RS1",
                    RouteLink=[
                        TXCRouteLink(
                            id="RL1",
                            From="2400A039650A",
                            To="2400A050290A",
                        )
                    ],
                ),
                RouteSection(
                    id="RS2",
                    RouteLink=[
                        TXCRouteLink(
                            id="RL2",
                            From="2400A050290A",
                            To="240096719",
                        )
                    ],
                ),
            ],
            id="Multiple RouteSections",
        ),
        pytest.param(
            """
        <RouteSections></RouteSections>
        """,
            [],
            id="Empty RouteSections",
        ),
        pytest.param(
            """
        <InvalidTopLevel />
        """,
            [],
            id="Invalid Top-level Element",
        ),
        pytest.param(
            """
        <TransXChange>
            <RouteSections>
                <RouteSection id="RS1"
                              CreationDateTime="2023-05-15T10:30:00+00:00"
                              ModificationDateTime="2023-05-16T12:45:00+00:00">
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
            </RouteSections>
        </TransXChange>
        """,
            [
                RouteSection(
                    id="RS1",
                    CreationDateTime=datetime(2023, 5, 15, 10, 30, tzinfo=timezone.utc),
                    ModificationDateTime=datetime(
                        2023, 5, 16, 12, 45, tzinfo=timezone.utc
                    ),
                    RouteLink=[
                        TXCRouteLink(
                            id="RL1",
                            From="2400A039650A",
                            To="2400A050290A",
                            CreationDateTime=datetime(
                                2023, 5, 15, 10, 30, tzinfo=timezone.utc
                            ),
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
                                        TXCLocation(
                                            id="loc2", Longitude="0.0", Latitude="0.0"
                                        ),
                                    ]
                                )
                            ),
                        )
                    ],
                )
            ],
            id="Valid RouteSection with Complete Details",
        ),
        pytest.param(
            """
        <TransXChange>
            <RouteSections>
                <RouteSection id="RS1">
                    <RouteLink id="RL1">
                        <From>
                            <StopPointRef>2400A039650A</StopPointRef>
                        </From>
                        <To>
                            <StopPointRef>2400A050290A</StopPointRef>
                        </To>
                    </RouteLink>
                </RouteSection>
                <RouteSection id="RS2">
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
            </RouteSections>
        </TransXChange>
        """,
            [
                RouteSection(
                    id="RS1",
                    CreationDateTime=None,
                    ModificationDateTime=None,
                    RouteLink=[
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
                        )
                    ],
                ),
                RouteSection(
                    id="RS2",
                    CreationDateTime=None,
                    ModificationDateTime=None,
                    RouteLink=[
                        TXCRouteLink(
                            id="RL2",
                            From="2400A050290A",
                            To="240096719",
                            CreationDateTime=datetime(
                                2023, 5, 17, 9, 0, tzinfo=timezone.utc
                            ),
                            ModificationDateTime=datetime(
                                2023, 5, 18, 14, 30, tzinfo=timezone.utc
                            ),
                            Modification="new",
                            RevisionNumber=1,
                            Distance=800,
                            Track=None,
                        )
                    ],
                ),
            ],
            id="Multiple RouteSections with Mixed Details",
        ),
        pytest.param(
            """
        <TransXChange>
            <InvalidSection />
        </TransXChange>
        """,
            [],
            id="Invalid Section",
        ),
    ],
)
def test_parse_route_sections(xml_string, expected):
    """
    Test the parsing of RouteSection list from XML.
    """
    root = etree.fromstring(xml_string)
    assert parse_route_sections(root, True) == expected
