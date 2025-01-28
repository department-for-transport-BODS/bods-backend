"""
Test Parsing OffStreet
"""

import pytest
from common_layer.txc.models.txc_stoppoint import (
    AirStopClassificationStructure,
    BayStructure,
    BusAndCoachStationStructure,
    FerryStopClassificationStructure,
    MetroStopClassificationStructure,
    OffStreetStructure,
    RailStopClassificationStructure,
)
from common_layer.txc.parser.stop_points.parse_stop_point_off_street import (
    parse_off_street_structure,
)
from lxml.etree import fromstring


@pytest.mark.parametrize(
    "off_street_xml_str, expected_result",
    [
        pytest.param(
            """
            <OffStreet>
                <BusAndCoach>
                    <Bay />
                </BusAndCoach>
            </OffStreet>
            """,
            OffStreetStructure(
                BusAndCoach=BusAndCoachStationStructure(
                    Bay=BayStructure(TimingStatus="principalTimingPoint")
                )
            ),
            id="Bus and Coach Station Bay",
        ),
        pytest.param(
            """
            <OffStreet>
                <BusAndCoach>
                    <Entrance />
                </BusAndCoach>
            </OffStreet>
            """,
            OffStreetStructure(
                BusAndCoach=BusAndCoachStationStructure(Entrance=True, Bay=None)
            ),
            id="Bus and Coach Station Bay",
        ),
        pytest.param(
            """
            <OffStreet>
                <Ferry>
                    <Entrance />
                </Ferry>
            </OffStreet>
            """,
            OffStreetStructure(Ferry=FerryStopClassificationStructure(Entrance=True)),
            id="Ferry Terminal Entrance",
        ),
        pytest.param(
            """
            <OffStreet>
                <Rail>
                    <Entrance />
                </Rail>
            </OffStreet>
            """,
            OffStreetStructure(Rail=RailStopClassificationStructure(Entrance=True)),
            id="Rail Station Entrance",
        ),
        pytest.param(
            """
            <OffStreet>
                <Metro>
                    <AccessArea />
                </Metro>
            </OffStreet>
            """,
            OffStreetStructure(Metro=MetroStopClassificationStructure(AccessArea=True)),
            id="Metro Station Access Area",
        ),
        pytest.param(
            """
            <OffStreet>
                <Metro>
                    <Entrance />
                </Metro>
            </OffStreet>
            """,
            OffStreetStructure(Metro=MetroStopClassificationStructure(Entrance=True)),
            id="Metro Station Entrance",
        ),
        pytest.param(
            """
            <OffStreet>
                <Metro>
                    <Platform />
                </Metro>
            </OffStreet>
            """,
            OffStreetStructure(Metro=MetroStopClassificationStructure(Platform=True)),
            id="Metro Station Platform",
        ),
        pytest.param(
            """
            <OffStreet>
                <Metro>
                    <Entrance />
                    <AccessArea />
                </Metro>
            </OffStreet>
            """,
            OffStreetStructure(
                Metro=MetroStopClassificationStructure(Entrance=True, AccessArea=True)
            ),
            id="Metro Station with Multiple Elements",
        ),
        pytest.param(
            """
            <OffStreet>
                <Air>
                    <Entrance />
                </Air>
            </OffStreet>
            """,
            OffStreetStructure(Air=AirStopClassificationStructure(Entrance=True)),
            id="Airport Entrance",
        ),
        pytest.param(
            """
            <OffStreet>
                <Air>
                    <AccessArea />
                </Air>
            </OffStreet>
            """,
            OffStreetStructure(Air=AirStopClassificationStructure(AccessArea=True)),
            id="Airport AccessArea",
        ),
        pytest.param(
            """
            <OffStreet>
                <Metro>
                </Metro>
            </OffStreet>
            """,
            None,
            id="Empty Metro Element",
        ),
        pytest.param(
            """
            <OffStreet>
            </OffStreet>
            """,
            None,
            id="Empty OffStreet Element",
        ),
    ],
)
def test_parse_off_street_structure(
    off_street_xml_str: str, expected_result: OffStreetStructure | None
):
    """
    OffStreet Structure Parsing test
    """
    off_street_xml = fromstring(off_street_xml_str)
    assert parse_off_street_structure(off_street_xml) == expected_result
