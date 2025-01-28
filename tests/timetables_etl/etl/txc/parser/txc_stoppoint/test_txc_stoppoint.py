"""
TXC Stoppoint XML to Pydantic Test
"""

import pytest
from common_layer.txc.models import (
    BearingStructure,
    BusStopStructure,
    DescriptorStructure,
    LocationStructure,
    MarkedPointStructure,
    OnStreetStructure,
    PlaceStructure,
    StopClassificationStructure,
    TXCStopPoint,
)
from common_layer.txc.parser.stop_points import parse_txc_stop_point
from lxml.etree import fromstring


@pytest.mark.parametrize(
    "stop_xml_str, expected_result",
    [
        pytest.param(
            """
            <StopPoint>
                <AtcoCode>900000001</AtcoCode>
                <Descriptor>
                    <CommonName>Stop 1</CommonName>
                </Descriptor>
                <Place>
                    <NptgLocalityRef>N0075743</NptgLocalityRef>
                    <Location>
                        <Translation>
                            <Longitude>-6.253318</Longitude>
                            <Latitude>53.347398</Latitude>
                            <Easting>117018</Easting>
                            <Northing>391827</Northing>
                        </Translation>
                    </Location>
                </Place>
                <StopClassification>
                    <StopType>busCoachTrolleyOnStreetPoint</StopType>
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
                </StopClassification>
                <StopAreas>Area1</StopAreas>
                <StopAreas>Area2</StopAreas>
                <AdministrativeAreaRef>AdministrativeArea1</AdministrativeAreaRef>
            </StopPoint>
            """,
            TXCStopPoint(
                AtcoCode="900000001",
                Descriptor=DescriptorStructure(CommonName="Stop 1"),
                Place=PlaceStructure(
                    NptgLocalityRef="N0075743",
                    Location=LocationStructure(
                        Longitude="-6.253318",
                        Latitude="53.347398",
                        Easting="117018",
                        Northing="391827",
                    ),
                ),
                StopClassification=StopClassificationStructure(
                    StopType="busCoachTrolleyOnStreetPoint",
                    OnStreet=OnStreetStructure(
                        Bus=BusStopStructure(
                            BusStopType="MKD",
                            TimingStatus="principalTimingPoint",
                            MarkedPoint=MarkedPointStructure(
                                Bearing=BearingStructure(CompassPoint="N")
                            ),
                        )
                    ),
                ),
                StopAreas=["Area1", "Area2"],
                AdministrativeAreaRef="AdministrativeArea1",
            ),
            id="Valid TXCStopPoint with StopAreas",
        ),
        pytest.param(
            """
            <StopPoint>
                <AtcoCode>900000002</AtcoCode>
                <Descriptor>
                    <CommonName>Stop 2</CommonName>
                </Descriptor>
                <Place>
                    <NptgLocalityRef>N0075744</NptgLocalityRef>
                    <Location>
                        <Translation>
                            <Longitude>-6.253318</Longitude>
                            <Latitude>53.347398</Latitude>
                            <Easting>117018</Easting>
                            <Northing>391827</Northing>
                        </Translation>
                    </Location>
                </Place>
                <StopClassification>
                    <StopType>busCoachTrolleyOnStreetPoint</StopType>
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
                </StopClassification>
                <AdministrativeAreaRef>AdministrativeArea2</AdministrativeAreaRef>
            </StopPoint>
            """,
            TXCStopPoint(
                AtcoCode="900000002",
                Descriptor=DescriptorStructure(CommonName="Stop 2"),
                Place=PlaceStructure(
                    NptgLocalityRef="N0075744",
                    Location=LocationStructure(
                        Longitude="-6.253318",
                        Latitude="53.347398",
                        Easting="117018",
                        Northing="391827",
                    ),
                ),
                StopClassification=StopClassificationStructure(
                    StopType="busCoachTrolleyOnStreetPoint",
                    OnStreet=OnStreetStructure(
                        Bus=BusStopStructure(
                            BusStopType="MKD",
                            TimingStatus="principalTimingPoint",
                            MarkedPoint=MarkedPointStructure(
                                Bearing=BearingStructure(CompassPoint="N")
                            ),
                        )
                    ),
                ),
                StopAreas=None,
                AdministrativeAreaRef="AdministrativeArea2",
            ),
            id="Valid TXCStopPoint without StopAreas",
        ),
        pytest.param(
            """
            <StopPoint>
                <Descriptor>
                    <CommonName>Stop 3</CommonName>
                </Descriptor>
                <Place>
                    <NptgLocalityRef>N0075745</NptgLocalityRef>
                    <Location>
                        <Longitude>-6.253318</Longitude>
                        <Latitude>53.347398</Latitude>
                        <Easting>117018</Easting>
                        <Northing>391827</Northing>
                    </Location>
                </Place>
                <StopClassification>
                    <StopType>busCoachTrolleyOnStreetPoint</StopType>
                    <OnStreet>
                        <Bus>
                            <BusStopType>MKD</BusStopType>
                            <TimingStatus>PTP</TimingStatus>
                            <MarkedPoint>
                                <Bearing>
                                    <CompassPoint>N</CompassPoint>
                                </Bearing>
                            </MarkedPoint>
                        </Bus>
                    </OnStreet>
                </StopClassification>
                <AdministrativeAreaRef>AdministrativeArea3</AdministrativeAreaRef>
            </StopPoint>
            """,
            None,
            id="Missing AtcoCode",
        ),
    ],
)
def test_parse_txc_stop_point(stop_xml_str: str, expected_result: TXCStopPoint | None):
    """
    Test Parsing a Stop Point
    """
    stop_xml = fromstring(stop_xml_str)
    assert parse_txc_stop_point(stop_xml) == expected_result
