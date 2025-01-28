"""
Test Parsing Annotated Stop Point Refs
"""

import pytest
from common_layer.txc.models import AnnotatedStopPointRef
from common_layer.txc.parser.stop_points import parse_stop_points
from lxml.etree import fromstring


@pytest.mark.parametrize(
    "xml_input, expected_output",
    [
        pytest.param(
            """
            <TransXChange>
            <StopPoints>
                <AnnotatedStopPointRef>
                    <StopPointRef>490014051VC</StopPointRef>
                    <CommonName>Victoria Coach Station</CommonName>
                    <LocalityName>Belgravia</LocalityName>
                    <LocalityQualifier>Victoria</LocalityQualifier>
                </AnnotatedStopPointRef>
            </StopPoints>
            </TransXChange>
            """,
            [
                AnnotatedStopPointRef(
                    StopPointRef="490014051VC",
                    CommonName="Victoria Coach Station",
                    Indicator=None,
                    LocalityName="Belgravia",
                    LocalityQualifier="Victoria",
                )
            ],
            id="Single Stop With Full Location Details",
        ),
        pytest.param(
            """
            <TransXChange>
            <StopPoints>
                <AnnotatedStopPointRef>
                    <StopPointRef>490014051VC</StopPointRef>
                    <CommonName>Victoria Coach Station</CommonName>
                </AnnotatedStopPointRef>
                <AnnotatedStopPointRef>
                    <StopPointRef>490016736W</StopPointRef>
                    <CommonName>London Victoria Coach Station Arrivals</CommonName>
                    <Indicator>Arrivals</Indicator>
                </AnnotatedStopPointRef>
            </StopPoints>
            </TransXChange>
            """,
            [
                AnnotatedStopPointRef(
                    StopPointRef="490014051VC",
                    CommonName="Victoria Coach Station",
                    Indicator=None,
                    LocalityName=None,
                    LocalityQualifier=None,
                ),
                AnnotatedStopPointRef(
                    StopPointRef="490016736W",
                    CommonName="London Victoria Coach Station Arrivals",
                    Indicator="Arrivals",
                    LocalityName=None,
                    LocalityQualifier=None,
                ),
            ],
            id="Multiple Stops With Different Optional Fields",
        ),
        pytest.param(
            """
            <StopPoints></StopPoints>
            """,
            [],
            id="Empty Stop Points",
        ),
        pytest.param(
            """
            <InvalidTopLevel></InvalidTopLevel>
            """,
            [],
            id="Invalid Top Level Element",
        ),
    ],
)
def test_parse_annoted_stop_point_ref(
    xml_input: str, expected_output: list[AnnotatedStopPointRef]
):
    """
    Test the generation of stop point pydantic models.

    """
    xml_data = fromstring(xml_input)
    stoppoints = parse_stop_points(xml_data)
    assert stoppoints == expected_output
