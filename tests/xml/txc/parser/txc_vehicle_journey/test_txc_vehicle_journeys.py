"""
Test Parsing of Vehinicle Journeys
"""

import pytest
from common_layer.xml.txc.models import (
    TXCBlock,
    TXCLayoverPoint,
    TXCOperational,
    TXCTicketMachine,
    TXCVehicleJourney,
)
from common_layer.xml.txc.parser.vehicle_journeys import (
    parse_layover_point,
    parse_operational,
    parse_vehicle_journey,
)
from lxml import etree
from pydantic import ValidationError

from tests.xml.conftest import assert_model_equal


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <Operational>
                <TicketMachine>
                    <JourneyCode>1</JourneyCode>
                </TicketMachine>
                <Block>
                    <Description>Block 1</Description>
                    <BlockNumber>B1</BlockNumber>
                </Block>
            </Operational>
            """,
            TXCOperational(
                TicketMachine=TXCTicketMachine(JourneyCode="1"),
                Block=TXCBlock(Description="Block 1", BlockNumber="B1"),
            ),
            id="Valid operational with ticket machine and block",
        ),
        pytest.param(
            """
            <Operational>
                <TicketMachine>
                    <JourneyCode>2</JourneyCode>
                </TicketMachine>
            </Operational>
            """,
            TXCOperational(TicketMachine=TXCTicketMachine(JourneyCode="2")),
            id="Valid operational with only ticket machine",
        ),
        pytest.param(
            """
            <Operational>
                <Block>
                    <Description>Block 2</Description>
                    <BlockNumber>B2</BlockNumber>
                </Block>
            </Operational>
            """,
            TXCOperational(Block=TXCBlock(Description="Block 2", BlockNumber="B2")),
            id="Valid operational with only block",
        ),
        pytest.param(
            """
            <Operational>
            </Operational>
            """,
            None,
            id="Empty operational",
        ),
    ],
)
def test_parse_operational(
    xml_string: str, expected_result: TXCOperational | None
) -> None:
    """
    Test Operational Section of Vehicle Journey parsing
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_operational(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <LayoverPoint>
                <Duration>PT10M</Duration>
                <Name>Layover Point 1</Name>
                <Location>123456</Location>
            </LayoverPoint>
            """,
            TXCLayoverPoint(
                Duration="PT10M",
                Name="Layover Point 1",
                Location="123456",
            ),
            id="Valid layover point",
        ),
        pytest.param(
            """
            <LayoverPoint>
                <Duration>PT15M</Duration>
                <Name>Layover Point 2</Name>
            </LayoverPoint>
            """,
            None,
            id="Invalid layover point missing Location",
        ),
        pytest.param(
            """
            <LayoverPoint>
                <Duration>PT20M</Duration>
                <Location>789012</Location>
            </LayoverPoint>
            """,
            None,
            id="Invalid layover point missing Name",
        ),
        pytest.param(
            """
            <LayoverPoint>
                <Name>Layover Point 3</Name>
                <Location>345678</Location>
            </LayoverPoint>
            """,
            None,
            id="Invalid layover point missing Duration",
        ),
        pytest.param(
            """
            <LayoverPoint>
            </LayoverPoint>
            """,
            None,
            id="Empty layover point",
        ),
    ],
)
def test_parse_layover_point(
    xml_string: str, expected_result: TXCLayoverPoint | None
) -> None:
    """
    Layover Points Parsing
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_layover_point(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <VehicleJourney>
                <VehicleJourneyCode>VJ1</VehicleJourneyCode>
                <OperatorRef>OP1</OperatorRef>
                <DepartureTime>10:00:00</DepartureTime>
                <JourneyPatternRef>JP1</JourneyPatternRef>
                <CommercialBasis>notContracted</CommercialBasis>
            </VehicleJourney>
            """,
            TXCVehicleJourney(
                VehicleJourneyCode="VJ1",
                OperatorRef="OP1",
                DepartureTime="10:00:00",
                JourneyPatternRef="JP1",
                CommercialBasis="notContracted",
            ),
            id="Valid",
        ),
        pytest.param(
            """
            <VehicleJourney>
                <VehicleJourneyCode>VJ2</VehicleJourneyCode>
                <OperatorRef>OP2</OperatorRef>
                <PrivateCode>PC1</PrivateCode>
                <DestinationDisplay>Destination</DestinationDisplay>
                <CommercialBasis>contracted</CommercialBasis>
                <DepartureTime>11:00:00</DepartureTime>
                <DepartureDayShift>+1</DepartureDayShift>
                <VehicleJourneyRef>VJ1</VehicleJourneyRef>
            </VehicleJourney>
            """,
            TXCVehicleJourney(
                OperatorRef="OP2",
                PrivateCode="PC1",
                DestinationDisplay="Destination",
                CommercialBasis="contracted",
                DepartureTime="11:00:00",
                DepartureDayShift=1,
                VehicleJourneyRef="VJ1",
                VehicleJourneyCode="VJ2",
            ),
            id="Valid: With optional fields",
        ),
        pytest.param(
            """
            <VehicleJourney>
                <VehicleJourneyCode>VJ2</VehicleJourneyCode>
                <OperatorRef>OP2</OperatorRef>
                <PrivateCode>PC1</PrivateCode>
                <DestinationDisplay>Destination</DestinationDisplay>
                <CommercialBasis>contracted</CommercialBasis>
                <DepartureTime>11:00:00</DepartureTime>
                <DepartureDayShift>+1</DepartureDayShift>
                <VehicleJourneyRef>VJ1</VehicleJourneyRef>
            </VehicleJourney>
            """,
            TXCVehicleJourney(
                OperatorRef="OP2",
                PrivateCode="PC1",
                DestinationDisplay="Destination",
                CommercialBasis="contracted",
                DepartureTime="11:00:00",
                DepartureDayShift=1,
                VehicleJourneyRef="VJ1",
                VehicleJourneyCode="VJ2",
            ),
            id="Valid: With positive day shift",
        ),
        pytest.param(
            """
            <VehicleJourney>
                <VehicleJourneyCode>VJ3</VehicleJourneyCode>
                <OperatorRef>OP2</OperatorRef>
                <PrivateCode>PC1</PrivateCode>
                <DestinationDisplay>Destination</DestinationDisplay>
                <CommercialBasis>contracted</CommercialBasis>
                <DepartureTime>23:00:00</DepartureTime>
                <DepartureDayShift>-1</DepartureDayShift>
                <VehicleJourneyRef>VJ1</VehicleJourneyRef>
            </VehicleJourney>
            """,
            TXCVehicleJourney(
                OperatorRef="OP2",
                PrivateCode="PC1",
                DestinationDisplay="Destination",
                CommercialBasis="contracted",
                DepartureTime="23:00:00",
                DepartureDayShift=-1,
                VehicleJourneyRef="VJ1",
                VehicleJourneyCode="VJ3",
            ),
            id="Valid: With negative day shift",
        ),
        pytest.param(
            """
            <VehicleJourney>
                <VehicleJourneyCode>VJ4</VehicleJourneyCode>
                <OperatorRef>OP2</OperatorRef>
                <PrivateCode>PC1</PrivateCode>
                <DestinationDisplay>Destination</DestinationDisplay>
                <CommercialBasis>contracted</CommercialBasis>
                <DepartureTime>12:00:00</DepartureTime>
                <DepartureDayShift>0</DepartureDayShift>
                <VehicleJourneyRef>VJ1</VehicleJourneyRef>
            </VehicleJourney>
            """,
            TXCVehicleJourney(
                OperatorRef="OP2",
                PrivateCode="PC1",
                DestinationDisplay="Destination",
                CommercialBasis="contracted",
                DepartureTime="12:00:00",
                DepartureDayShift=0,
                VehicleJourneyRef="VJ1",
                VehicleJourneyCode="VJ4",
            ),
            id="Valid: With zero day shift",
        ),
        pytest.param(
            """
            <VehicleJourney id="VJ6">
                <OperatorRef>OP6</OperatorRef>
            </VehicleJourney>
            """,
            None,
            id="Invalid: Missing DepartureTime",
        ),
    ],
)
def test_parse_vehicle_journey(
    xml_string: str, expected_result: TXCVehicleJourney
) -> None:
    """
    Parse XML for Vehicle Journey
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_vehicle_journey(xml_element)
    if result is not None:

        assert_model_equal(result, expected_result)
    else:
        assert expected_result == result


@pytest.mark.parametrize(
    "xml_string",
    [
        pytest.param(
            """
            <VehicleJourney id="VJ5">
                <DepartureTime>14:00:00</DepartureTime>
            </VehicleJourney>
            """,
            id="Invalid vehicle journey missing OperatorRef",
        ),
    ],
)
def test_parse_vehicle_journey_exception(xml_string: str) -> None:
    """
    Parse XML for Vehicle Journey
    """
    xml_element = etree.fromstring(xml_string)
    with pytest.raises(ValidationError):
        parse_vehicle_journey(xml_element)
