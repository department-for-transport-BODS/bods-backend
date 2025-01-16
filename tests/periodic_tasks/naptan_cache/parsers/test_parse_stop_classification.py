"""
Test Parsing Stop Classification
"""

import pytest
from lxml import etree

from periodic_tasks.naptan_cache.app.data_loader.parsers.parser_stop_classification import (
    extract_bus_stop_type,
    parse_stop_classification,
)
from tests.periodic_tasks.naptan_cache.parsers.common import (
    NAPTAN_PREFIX,
    create_stop_point,
    parse_xml_to_stop_point,
)


@pytest.mark.parametrize(
    ("xml_input", "expected"),
    [
        pytest.param(
            create_stop_point(
                """
                <StopClassification>
                    <OnStreet>
                        <Bus>
                            <BusStopType>MKD</BusStopType>
                            <TimingStatus>OTH</TimingStatus>
                            <MarkedPoint>
                                <Bearing>
                                    <CompassPoint>E</CompassPoint>
                                </Bearing>
                            </MarkedPoint>
                        </Bus>
                    </OnStreet>
                </StopClassification>
            """
            ),
            "MKD",
            id="Simple BusStopType",
        ),
        pytest.param(
            create_stop_point(
                """
                <StopClassification>
                    <OnStreet>
                        <Bus>
                            <BusStopType>MKD</BusStopType>
                            <TimingStatus>OTH</TimingStatus>
                            <MarkedPoint>
                                <Bearing>
                                    <CompassPoint>NW</CompassPoint>
                                </Bearing>
                            </MarkedPoint>
                        </Bus>
                    </OnStreet>
                </StopClassification>
            """
            ),
            "MKD",
            id="BusStopType With Other Data",
        ),
        pytest.param(
            create_stop_point(
                """
                <StopClassification>
                    <OnStreet>
                        <Bus>
                            <TimingStatus>OTH</TimingStatus>
                        </Bus>
                    </OnStreet>
                </StopClassification>
            """
            ),
            None,
            id="No BusStopType",
        ),
        pytest.param(
            create_stop_point(
                """
                <StopClassification>
                    <OnStreet>
                        <Bus>
                            <BusStopType></BusStopType>
                        </Bus>
                    </OnStreet>
                </StopClassification>
            """
            ),
            None,
            id="Empty BusStopType",
        ),
        pytest.param(
            create_stop_point(
                """
                <StopClassification>
                    <OnStreet>
                        <OtherMode>
                            <BusStopType>MKD</BusStopType>
                        </OtherMode>
                    </OnStreet>
                </StopClassification>
            """
            ),
            None,
            id="Wrong Container",
        ),
        pytest.param(
            create_stop_point(
                """
                <StopClassification>
                    <OnStreet></OnStreet>
                </StopClassification>
            """
            ),
            None,
            id="Empty OnStreet",
        ),
    ],
)
def test_extract_bus_stop_type(xml_input: str, expected: str | None) -> None:
    """
    Test extract_bus_stop_type function with various input scenarios.
    """
    stop_point: etree._Element = parse_xml_to_stop_point(xml_input)
    onstreet_element = stop_point.find(f".//{NAPTAN_PREFIX}OnStreet")
    if onstreet_element is None:
        raise ValueError("OnStreet element not found")
    result: str | None = extract_bus_stop_type(onstreet_element)
    assert result == expected


@pytest.mark.parametrize(
    ("xml_input", "expected"),
    [
        pytest.param(
            create_stop_point(
                """
               <StopClassification>
                   <StopType>BCT</StopType>
                   <OnStreet>
                       <Bus>
                           <BusStopType>MKD</BusStopType>
                           <TimingStatus>OTH</TimingStatus>
                           <MarkedPoint>
                               <Bearing>
                                   <CompassPoint>E</CompassPoint>
                               </Bearing>
                           </MarkedPoint>
                       </Bus>
                   </OnStreet>
               </StopClassification>
           """
            ),
            {
                "StopType": "BCT",
                "BusStopType": "MKD",
            },
            id="CompleteClassificationData",
        ),
        pytest.param(
            create_stop_point(
                """
               <StopClassification>
                   <StopType>BCT</StopType>
               </StopClassification>
           """
            ),
            {
                "StopType": "BCT",
                "BusStopType": None,
            },
            id="OnlyStopType",
        ),
        pytest.param(
            create_stop_point(
                """
               <StopClassification>
                   <OnStreet>
                       <Bus>
                           <BusStopType>MKD</BusStopType>
                       </Bus>
                   </OnStreet>
               </StopClassification>
           """
            ),
            {
                "StopType": None,
                "BusStopType": "MKD",
            },
            id="OnlyBusStopType",
        ),
        pytest.param(
            create_stop_point(
                """
               <StopClassification>
                   <OnStreet>
                       <Bus>
                           <TimingStatus>OTH</TimingStatus>
                       </Bus>
                   </OnStreet>
               </StopClassification>
           """
            ),
            {
                "StopType": None,
                "BusStopType": None,
            },
            id="OnlyOtherBusData",
        ),
        pytest.param(
            create_stop_point(
                """
               <StopClassification>
                   <StopType></StopType>
                   <OnStreet>
                       <Bus>
                           <BusStopType></BusStopType>
                       </Bus>
                   </OnStreet>
               </StopClassification>
           """
            ),
            {
                "StopType": None,
                "BusStopType": None,
            },
            id="EmptyElements",
        ),
        pytest.param(
            create_stop_point("<StopClassification></StopClassification>"),
            {
                "StopType": None,
                "BusStopType": None,
            },
            id="EmptyClassification",
        ),
        pytest.param(
            create_stop_point(""),
            {
                "StopType": None,
                "BusStopType": None,
            },
            id="NoClassification",
        ),
    ],
)
def test_parse_stop_classification(
    xml_input: str, expected: dict[str, str | None]
) -> None:
    """
    Test parse_stop_classification function with various input scenarios.
    """
    stop_point: etree._Element = parse_xml_to_stop_point(xml_input)
    result: dict[str, str | None] = parse_stop_classification(stop_point)
    assert result == expected
