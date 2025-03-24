"""
Parse Bus type StopClassification
"""

import pytest
from common_layer.xml.txc.models import (
    BearingStructure,
    BusStopStructure,
    LocationStructure,
    MarkedPointStructure,
)
from common_layer.xml.txc.models.txc_stoppoint.stop_point_types_bus import (
    FlexibleZoneStructure,
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
        pytest.param(
            """
            <Bus>
                <BusStopType>custom</BusStopType>
                <TimingStatus>principalTimingPoint</TimingStatus>
                <MarkedPoint>
                    <Bearing>
                        <CompassPoint>N</CompassPoint>
                    </Bearing>
                </MarkedPoint>
            </Bus>
            """,
            BusStopStructure(
                BusStopType="custom",
                TimingStatus="principalTimingPoint",
                MarkedPoint=MarkedPointStructure(
                    Bearing=BearingStructure(CompassPoint="N")
                ),
            ),
            id="Custom BusStopType with MarkedPoint",
        ),
        pytest.param(
            """
        <Bus>
            <BusStopType>FLX</BusStopType>
            <TimingStatus>OTH</TimingStatus>
            <FlexibleZone>
                <Location>
                    <Easting>462732</Easting>
                    <Northing>172119</Northing>
                </Location>
                <Location>
                <Translation>
                    <Easting>401187</Easting>
                    <Northing>377271</Northing>
                    <Longitude>-1.9836500</Longitude>
                    <Latitude>53.2924256</Latitude>
                </Translation>
                </Location>
            </FlexibleZone>
        </Bus>
        """,
            BusStopStructure(
                BusStopType="FLX",
                TimingStatus="otherPoint",
                FlexibleZone=FlexibleZoneStructure(
                    Location=[
                        LocationStructure(
                            Easting="462732",
                            Northing="172119",
                            Longitude=None,
                            Latitude=None,
                        ),
                        LocationStructure(
                            Easting="462636",
                            Northing="172042",
                            Longitude="1.9836500",
                            Latitude="53.2924256",
                        ),
                    ]
                ),
            ),
            id="FLX bus stop with FlexibleZone",
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
