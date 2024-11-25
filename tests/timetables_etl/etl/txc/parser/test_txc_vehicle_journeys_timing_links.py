"""
Test Parsing Vehicle Journey Timing Links
"""

import pytest
from lxml import etree

from timetables_etl.etl.app.txc.models.txc_vehicle_journey import (
    TXCVehicleJourneyStopUsageStructure,
    TXCVehicleJourneyTimingLink,
)
from timetables_etl.etl.app.txc.parser.vehicle_journeys import (
    parse_vehicle_journey_stop_usage,
    parse_vehicle_journey_timing_link,
    parse_vehicle_journey_timing_links,
)


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <From>
                <WaitTime>PT5M</WaitTime>
                <DynamicDestinationDisplay>Destination 1</DynamicDestinationDisplay>
                <Activity>pickUp</Activity>
            </From>
            """,
            TXCVehicleJourneyStopUsageStructure(
                WaitTime="PT5M",
                DynamicDestinationDisplay="Destination 1",
            ),
            id="Valid stop usage with all fields",
        ),
        pytest.param(
            """
            <To>
                <WaitTime>PT10M</WaitTime>
            </To>
            """,
            TXCVehicleJourneyStopUsageStructure(WaitTime="PT10M"),
            id="Valid stop usage with only wait time",
        ),
        pytest.param(
            """
            <From>
                <DynamicDestinationDisplay>Destination 2</DynamicDestinationDisplay>
            </From>
            """,
            TXCVehicleJourneyStopUsageStructure(
                DynamicDestinationDisplay="Destination 2"
            ),
            id="Valid stop usage with only dynamic destination display",
        ),
        pytest.param(
            """
            <To>
                <Activity>setDown</Activity>
            </To>
            """,
            TXCVehicleJourneyStopUsageStructure(),
            id="Valid stop usage with only activity (Not allowed in PTI)",
        ),
        pytest.param(
            """
            <From>
            </From>
            """,
            None,
            id="Empty stop usage",
        ),
    ],
)
def test_parse_vehicle_journey_stop_usage(xml_string, expected_result):
    """
    Test parsing of VehicleJourneyStopUsageStructure (From/To) section
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_vehicle_journey_stop_usage(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <VehicleJourneyTimingLink id="VJTL1">
                <JourneyPatternTimingLinkRef>JPTL1</JourneyPatternTimingLinkRef>
                <VehicleJourneyRef>VJ1</VehicleJourneyRef>
                <RunTime>PT30M</RunTime>
                <From>
                    <WaitTime>PT5M</WaitTime>
                </From>
                <To>
                    <Activity>setDown</Activity>
                </To>
            </VehicleJourneyTimingLink>
            """,
            TXCVehicleJourneyTimingLink(
                id="VJTL1",
                JourneyPatternTimingLinkRef="JPTL1",
                VehicleJourneyRef="VJ1",
                RunTime="PT30M",
                From=TXCVehicleJourneyStopUsageStructure(WaitTime="PT5M"),
                To=TXCVehicleJourneyStopUsageStructure(),
            ),
            id="Valid timing link with all fields",
        ),
    ],
)
def test_parse_vehicle_journey_timing_link(xml_string, expected_result):
    """
    Test parsing of VehicleJourneyTimingLink section
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_vehicle_journey_timing_link(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <VehicleJourney>
                <VehicleJourneyTimingLink id="VJTL1">
                    <JourneyPatternTimingLinkRef>JPTL1</JourneyPatternTimingLinkRef>
                    <RunTime>PT30M</RunTime>
                </VehicleJourneyTimingLink>
                <VehicleJourneyTimingLink id="VJTL2">
                    <JourneyPatternTimingLinkRef>JPTL2</JourneyPatternTimingLinkRef>
                    <RunTime>PT15M</RunTime>
                    <From>
                        <WaitTime>PT5M</WaitTime>
                    </From>
                </VehicleJourneyTimingLink>
            </VehicleJourney>
            """,
            [
                TXCVehicleJourneyTimingLink(
                    id="VJTL1",
                    JourneyPatternTimingLinkRef="JPTL1",
                    RunTime="PT30M",
                ),
                TXCVehicleJourneyTimingLink(
                    id="VJTL2",
                    JourneyPatternTimingLinkRef="JPTL2",
                    RunTime="PT15M",
                    From=TXCVehicleJourneyStopUsageStructure(WaitTime="PT5M"),
                ),
            ],
            id="Valid vehicle journey with multiple timing links",
        ),
        pytest.param(
            """
            <VehicleJourney>
            </VehicleJourney>
            """,
            [],
            id="Empty vehicle journey",
        ),
    ],
)
def test_parse_vehicle_journey_timing_links(xml_string, expected_result):
    """
    Test parsing of all VehicleJourneyTimingLink sections
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_vehicle_journey_timing_links(xml_element)
    assert result == expected_result
