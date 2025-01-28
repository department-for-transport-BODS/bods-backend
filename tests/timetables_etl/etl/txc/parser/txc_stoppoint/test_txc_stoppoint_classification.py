"""
Test Parsing StopClassification
"""

import pytest
from common_layer.txc.models.txc_stoppoint import (
    BayStructure,
    BearingStructure,
    BusAndCoachStationStructure,
    BusStopStructure,
    FerryStopClassificationStructure,
    MarkedPointStructure,
    OffStreetStructure,
    OnStreetStructure,
    RailStopClassificationStructure,
    StopClassificationStructure,
)
from common_layer.txc.parser.stop_points import parse_stop_classification_structure
from lxml.etree import fromstring


@pytest.mark.parametrize(
    "stop_classification_xml_str, expected_result",
    [
        pytest.param(
            """
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
            """,
            StopClassificationStructure(
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
            id="Valid Stop Classification Structure",
        ),
        pytest.param(
            """
            <StopClassification>
                <StopType>BCS</StopType>
                <OffStreet>
                    <BusAndCoach>
                        <Bay />
                    </BusAndCoach>
                </OffStreet>
            </StopClassification>
            """,
            StopClassificationStructure(
                StopType="busCoachTrolleyStationBay",
                OffStreet=OffStreetStructure(
                    BusAndCoach=BusAndCoachStationStructure(
                        Bay=BayStructure(TimingStatus="principalTimingPoint")
                    )
                ),
            ),
            id="Valid Bus Coach Station Bay Structure",
        ),
        pytest.param(
            """
            <StopClassification>
                <StopType>FTD</StopType>
                <OffStreet>
                    <Ferry>
                        <Entrance />
                    </Ferry>
                </OffStreet>
            </StopClassification>
            """,
            StopClassificationStructure(
                StopType="ferryTerminalDockEntrance",
                OffStreet=OffStreetStructure(
                    Ferry=FerryStopClassificationStructure(Entrance=True)
                ),
            ),
            id="Valid Ferry Terminal Structure",
        ),
        pytest.param(
            """
            <StopClassification>
                <StopType>RSE</StopType>
                <OffStreet>
                    <Rail>
                        <Entrance />
                    </Rail>
                </OffStreet>
            </StopClassification>
            """,
            StopClassificationStructure(
                StopType="railStationEntrance",
                OffStreet=OffStreetStructure(
                    Rail=RailStopClassificationStructure(Entrance=True)
                ),
            ),
            id="Valid Rail Station Structure",
        ),
        pytest.param(
            """
            <StopClassification>
                <StopType>busCoachTrolleyOnStreetPoint</StopType>
            </StopClassification>
            """,
            None,
            id="Missing OnStreet XML",
        ),
        pytest.param(
            """
            <StopClassification>
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
            """,
            None,
            id="Missing Stop Type",
        ),
    ],
)
def test_parse_stop_classification_structure(
    stop_classification_xml_str: str, expected_result: StopClassificationStructure
):
    """
    Stop Classification Parsing test
    """
    stop_classification_xml = fromstring(stop_classification_xml_str)
    assert (
        parse_stop_classification_structure(stop_classification_xml) == expected_result
    )
