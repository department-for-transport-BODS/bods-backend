"""
Parse Bus type StopClassification
"""

import pytest
from common_layer.xml.txc.models import (
    BearingStructure,
    BusStopStructure,
    MarkedPointStructure,
)
from common_layer.xml.txc.parser.stop_points.parse_stop_point_on_street import (
    parse_bus_stop_structure,
)
from lxml.etree import fromstring


@pytest.mark.parametrize(
    "bus_xml_str, expected_result",
    [
        # Valid BusStopStructure
        pytest.param(
            """
            <Bus>
                <BusStopType>MKD</BusStopType>
                <TimingStatus>principalTimingPoint</TimingStatus>
                <MarkedPoint>
                    <Bearing>
                        <CompassPoint>N</CompassPoint>
                    </Bearing>
                </MarkedPoint>
            </Bus>
            """,
            BusStopStructure(
                BusStopType="MKD",
                TimingStatus="principalTimingPoint",
                MarkedPoint=MarkedPointStructure(
                    Bearing=BearingStructure(CompassPoint="N")
                ),
            ),
            id="Correctly Parse",
        ),
        pytest.param(
            """
            <Bus>
                <TimingStatus>principalTimingPoint</TimingStatus>
                <MarkedPoint>
                    <Bearing>
                        <CompassPoint>N</CompassPoint>
                    </Bearing>
                </MarkedPoint>
            </Bus>
            """,
            None,
            id="Missing BusStopType",
        ),
        pytest.param(
            """
            <Bus>
                <BusStopType>MKD</BusStopType>
                <TimingStatus>InvalidStatus</TimingStatus>
                <MarkedPoint>
                    <Bearing>
                        <CompassPoint>N</CompassPoint>
                    </Bearing>
                </MarkedPoint>
            </Bus>
            """,
            None,
            id="Missing TimingStatus",
        ),
    ],
)
def test_parse_bus_stop_structure(
    bus_xml_str: str, expected_result: BusStopStructure | None
):
    """
    Parsing of Bus Stop Structure
    """
    bus_xml = fromstring(bus_xml_str)
    assert parse_bus_stop_structure(bus_xml) == expected_result
