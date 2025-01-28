"""
Parse Bus type StopClassification
"""

import pytest
from common_layer.txc.models.txc_stoppoint import UnmarkedPointStructure
from common_layer.txc.models.txc_stoppoint.stop_point_marked import (
    BearingStructure,
    MarkedPointStructure,
)
from common_layer.txc.models.txc_stoppoint.stop_point_types_bus import BusStopStructure
from common_layer.txc.models.txc_stoppoint.stoppoint_classification import (
    OnStreetStructure,
)
from common_layer.txc.parser.stop_points import (
    parse_bus_stop_structure,
    parse_on_street_structure,
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


@pytest.mark.parametrize(
    "on_street_xml_str, expected_result",
    [
        pytest.param(
            """
            <OnStreet>
                <Bus>
                    <BusStopType>MKD</BusStopType>
                    <TimingStatus>principalTimingPoint</TimingStatus>
                    <MarkedPoint>
                        <Bearing>
                            <CompassPoint>N</CompassPoint>
                        </Bearing>
                    </MarkedPoint>
                </Bus>
            </OnStreet>
            """,
            OnStreetStructure(
                Bus=BusStopStructure(
                    BusStopType="MKD",
                    TimingStatus="principalTimingPoint",
                    MarkedPoint=MarkedPointStructure(
                        Bearing=BearingStructure(CompassPoint="N")
                    ),
                )
            ),
            id="Valid OnStreet Structure",
        ),
        pytest.param(
            "<OnStreet></OnStreet>",
            None,
            id="Missing Bus XML",
        ),
        pytest.param(
            """
            <OnStreet>
                <Bus>
                    <BusStopType>CUS</BusStopType>
                    <TimingStatus>OTH</TimingStatus>
                    <UnmarkedPoint>
                        <Bearing>
                            <CompassPoint>NE</CompassPoint>
                        </Bearing>
                    </UnmarkedPoint>
                </Bus>
            </OnStreet>
            """,
            OnStreetStructure(
                Bus=BusStopStructure(
                    BusStopType="custom",
                    TimingStatus="otherPoint",
                    UnmarkedPoint=UnmarkedPointStructure(
                        Bearing=BearingStructure(CompassPoint="NE")
                    ),
                )
            ),
            id="Valid OnStreet Structure with UnmarkedPoint",
        ),
        pytest.param(
            """
            <OnStreet>
                <Bus>
                    <BusStopType>InvalidType</BusStopType>
                    <TimingStatus>principalTimingPoint</TimingStatus>
                    <MarkedPoint>
                        <Bearing>
                            <CompassPoint>N</CompassPoint>
                        </Bearing>
                    </MarkedPoint>
                </Bus>
            </OnStreet>
            """,
            None,
            id="Invalid Bus Stop Structure",
        ),
    ],
)
def test_parse_on_street_structure(
    on_street_xml_str: str, expected_result: OnStreetStructure | None
):
    """
    Test Parsing On Street Structure
    """
    on_street_xml = fromstring(on_street_xml_str)
    assert parse_on_street_structure(on_street_xml) == expected_result
