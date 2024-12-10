"""
Flexible Vehicle Journey PArsing Tests
"""

import pytest
from lxml import etree
from pydantic import ValidationError

from timetables_etl.etl.app.txc.models import (
    TXCFlexibleServiceTimes,
    TXCFlexibleVehicleJourney,
    TXCServicePeriod,
)
from timetables_etl.etl.app.txc.parser.vehicle_journeys_flexible import (
    parse_flexible_service_times,
    parse_flexible_vehicle_journey,
)

from .utils import assert_model_equal


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <FlexibleServiceTimes>
                <ServicePeriod>
                    <StartTime>07:00:00</StartTime>
                    <EndTime>19:00:00</EndTime>
                </ServicePeriod>
            </FlexibleServiceTimes>
            """,
            [
                TXCFlexibleServiceTimes(
                    ServicePeriod=TXCServicePeriod(
                        StartTime="07:00:00", EndTime="19:00:00"
                    )
                )
            ],
            id="Single service period",
        ),
        pytest.param(
            """
            <FlexibleServiceTimes>
                <AllDayService />
            </FlexibleServiceTimes>
            """,
            [TXCFlexibleServiceTimes(AllDayService=True)],
            id="Single all day service",
        ),
        pytest.param(
            """
            <FlexibleServiceTimes>
                <ServicePeriod>
                    <StartTime>07:00:00</StartTime>
                    <EndTime>12:00:00</EndTime>
                </ServicePeriod>
                <ServicePeriod>
                    <StartTime>13:00:00</StartTime>
                    <EndTime>19:00:00</EndTime>
                </ServicePeriod>
            </FlexibleServiceTimes>
            """,
            [
                TXCFlexibleServiceTimes(
                    ServicePeriod=TXCServicePeriod(
                        StartTime="07:00:00", EndTime="12:00:00"
                    )
                ),
                TXCFlexibleServiceTimes(
                    ServicePeriod=TXCServicePeriod(
                        StartTime="13:00:00", EndTime="19:00:00"
                    )
                ),
            ],
            id="Multiple service periods",
        ),
        pytest.param(
            """
            <FlexibleServiceTimes>
                <AllDayService />
                <AllDayService />
            </FlexibleServiceTimes>
            """,
            [
                TXCFlexibleServiceTimes(AllDayService=True),
                TXCFlexibleServiceTimes(AllDayService=True),
            ],
            id="Multiple all day services",
        ),
        pytest.param(
            """
            <FlexibleServiceTimes>
                <ServicePeriod>
                    <StartTime>07:00:00</StartTime>
                    <EndTime>19:00:00</EndTime>
                </ServicePeriod>
                <AllDayService />
            </FlexibleServiceTimes>
            """,
            [
                TXCFlexibleServiceTimes(
                    ServicePeriod=TXCServicePeriod(
                        StartTime="07:00:00", EndTime="19:00:00"
                    )
                ),
                TXCFlexibleServiceTimes(AllDayService=True),
            ],
            id="Mixed service period and all day service",
        ),
        pytest.param(
            """
            <FlexibleServiceTimes>
                <ServicePeriod>
                    <StartTime>08:00:00</StartTime>
                </ServicePeriod>
            </FlexibleServiceTimes>
            """,
            None,
            id="Invalid service period missing end time",
        ),
        pytest.param(
            """
            <FlexibleServiceTimes>
                <ServicePeriod>
                    <EndTime>18:00:00</EndTime>
                </ServicePeriod>
            </FlexibleServiceTimes>
            """,
            None,
            id="Invalid service period missing start time",
        ),
        pytest.param(
            """
            <FlexibleServiceTimes>
            </FlexibleServiceTimes>
            """,
            None,
            id="Empty flexible service times",
        ),
    ],
)
def test_parse_flexible_service_times(xml_string, expected_result):
    """
    Test FlexibleServiceTimes section parsing including multiple service times
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_flexible_service_times(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <FlexibleVehicleJourney>
                <DestinationDisplay>Flexible</DestinationDisplay>
                <Direction>outbound</Direction>
                <Description>Monday to Friday service</Description>
                <VehicleJourneyCode>vj_1</VehicleJourneyCode>
                <ServiceRef>PB0002032:467</ServiceRef>
                <LineRef>ARBB:PB0002032:467:53M</LineRef>
                <JourneyPatternRef>jp_1</JourneyPatternRef>
                <FlexibleServiceTimes>
                    <ServicePeriod>
                        <StartTime>07:00:00</StartTime>
                        <EndTime>19:00:00</EndTime>
                    </ServicePeriod>
                </FlexibleServiceTimes>
            </FlexibleVehicleJourney>
            """,
            TXCFlexibleVehicleJourney(
                DestinationDisplay="Flexible",
                Direction="outbound",
                Description="Monday to Friday service",
                VehicleJourneyCode="vj_1",
                ServiceRef="PB0002032:467",
                LineRef="ARBB:PB0002032:467:53M",
                JourneyPatternRef="jp_1",
                FlexibleServiceTimes=[
                    TXCFlexibleServiceTimes(
                        ServicePeriod=TXCServicePeriod(
                            StartTime="07:00:00", EndTime="19:00:00"
                        )
                    )
                ],
            ),
            id="Valid flexible journey with service period",
        ),
        pytest.param(
            """
            <FlexibleVehicleJourney>
                <Direction>outbound</Direction>
                <Description>All day service</Description>
                <VehicleJourneyCode>vj_2</VehicleJourneyCode>
                <ServiceRef>UZ000WOCT:216</ServiceRef>
                <LineRef>ARBB:UZ000WOCT:216:53M</LineRef>
                <JourneyPatternRef>jp_2</JourneyPatternRef>
                <FlexibleServiceTimes>
                    <AllDayService />
                </FlexibleServiceTimes>
            </FlexibleVehicleJourney>
            """,
            TXCFlexibleVehicleJourney(
                Direction="outbound",
                Description="All day service",
                VehicleJourneyCode="vj_2",
                ServiceRef="UZ000WOCT:216",
                LineRef="ARBB:UZ000WOCT:216:53M",
                JourneyPatternRef="jp_2",
                FlexibleServiceTimes=[TXCFlexibleServiceTimes(AllDayService=True)],
            ),
            id="Valid flexible journey with all day service",
        ),
        pytest.param(
            """
            <FlexibleVehicleJourney>
                <Direction>outbound</Direction>
                <VehicleJourneyCode>vj_3</VehicleJourneyCode>
                <ServiceRef>UZ000WOCT:216</ServiceRef>
                <LineRef>ARBB:UZ000WOCT:216:53M</LineRef>
                <JourneyPatternRef>jp_2</JourneyPatternRef>
            </FlexibleVehicleJourney>
            """,
            None,
            id="Invalid flexible journey missing FlexibleServiceTimes",
        ),
        pytest.param(
            """
            <FlexibleVehicleJourney>
                <Direction>outbound</Direction>
                <Description>Invalid service</Description>
                <FlexibleServiceTimes>
                    <ServicePeriod>
                        <StartTime>07:00:00</StartTime>
                        <EndTime>19:00:00</EndTime>
                    </ServicePeriod>
                </FlexibleServiceTimes>
            </FlexibleVehicleJourney>
            """,
            None,
            id="Invalid flexible journey missing required refs",
        ),
    ],
)
def test_parse_flexible_vehicle_journey(
    xml_string: str, expected_result: TXCFlexibleVehicleJourney | None
):
    """
    Test FlexibleVehicleJourney parsing
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_flexible_vehicle_journey(xml_element)
    if result is not None and expected_result is not None:
        assert_model_equal(result, expected_result)
    else:
        assert expected_result == result


@pytest.mark.parametrize(
    "xml_string",
    [
        pytest.param(
            """
            <FlexibleVehicleJourney>
                <VehicleJourneyCode>vj_4</VehicleJourneyCode>
                <ServiceRef>SERVICE1</ServiceRef>
                <LineRef>LINE1</LineRef>
                <Direction>invalid_direction</Direction>
                <FlexibleServiceTimes>
                    <AllDayService />
                </FlexibleServiceTimes>
            </FlexibleVehicleJourney>
            """,
            id="Invalid direction value",
        ),
    ],
)
def test_parse_flexible_vehicle_journey_validation_error(xml_string):
    """
    Test FlexibleVehicleJourney validation errors
    """
    xml_element = etree.fromstring(xml_string)
    with pytest.raises(ValidationError):
        parse_flexible_vehicle_journey(xml_element)
