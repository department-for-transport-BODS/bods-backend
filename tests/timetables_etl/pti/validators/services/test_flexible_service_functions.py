"""
Test Service Functions
"""

from unittest.mock import MagicMock

import pytest
from lxml import etree
from pti.app.validators.service.flexible_service import (
    check_flexible_service_times,
    check_flexible_service_timing_status,
    get_flexible_service_stop_point_ref_validator,
    has_flexible_service_classification,
)

NAMESPACE = {"x": "http://www.transxchange.org.uk/"}


@pytest.mark.parametrize(
    ("timing_status_values", "expected"),
    [
        pytest.param(
            ["otherPoint", "otherPoint", "otherPoint"],
            True,
            id="All Timing Points Are Other Point",
        ),
        pytest.param(
            ["otherPoint", "TXT", "otherPoint"], False, id="One Timing Point Is TXT"
        ),
        pytest.param(["", "", ""], False, id="All Timing Points Are Empty"),
        pytest.param(["XYZ", "ABC", ""], False, id="Mixed Invalid Timing Points"),
    ],
)
def test_check_flexible_service_timing_status(
    timing_status_values: list[str], expected: bool
):
    """
    Timing Status Test
    """
    xml = f"""
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" SchemaVersion="2.4">
        <Services>
            <Service>
                <FlexibleService>
                    <FlexibleJourneyPattern id="jp_1">
                        <StopPointsInSequence>
                            <FixedStopUsage SequenceNumber="1">
                                <StopPointRef>0600000102</StopPointRef>
                                <TimingStatus>{timing_status_values[0]}</TimingStatus>
                            </FixedStopUsage>
                            <FixedStopUsage SequenceNumber="2">
                                <StopPointRef>0600000101</StopPointRef>
                                <TimingStatus>{timing_status_values[1]}</TimingStatus>
                            </FixedStopUsage>
                            <FlexibleStopUsage>
                                <StopPointRef>270002700155</StopPointRef>
                            </FlexibleStopUsage>
                            <FixedStopUsage SequenceNumber="4">
                                <StopPointRef>0600000103</StopPointRef>
                                <TimingStatus>{timing_status_values[2]}</TimingStatus>
                            </FixedStopUsage>
                        </StopPointsInSequence>
                    </FlexibleJourneyPattern>
                </FlexibleService>
            </Service>
        </Services>
    </TransXChange>
    """
    doc = etree.fromstring(xml)
    elements = doc.xpath(
        "//x:Service/x:FlexibleService/x:FlexibleJourneyPattern", namespaces=NAMESPACE
    )
    actual = check_flexible_service_timing_status("", elements)
    assert actual == expected


@pytest.mark.parametrize(
    ("stop_refs", "compliant_count", "expected"),
    [
        pytest.param(
            ["270002700155", "270002700156"], 2, True, id="All Stops Are FLX Type"
        ),
        pytest.param(
            ["270002700156", "270002700157"], 1, False, id="One Stop Is Non FLX Type"
        ),
        pytest.param(
            ["270002700157", "270002700158"], 0, False, id="No Stops Are FLX Type"
        ),
    ],
)
def test_check_flexible_stops(
    m_stop_point_repo: MagicMock,
    stop_refs: list[str],
    compliant_count: int,
    expected: bool,
):
    """
    Test Spots of Flexible Service
    """
    m_stop_point_repo.return_value.get_count.return_value = compliant_count

    xml = f"""
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" SchemaVersion="2.4">
        <Services>
            <Service>
                <FlexibleService>
                    <FlexibleJourneyPattern id="jp_1">
                        <StopPointsInSequence>
                            <FlexibleStopUsage>
                                <StopPointRef>{stop_refs[0]}</StopPointRef>
                            </FlexibleStopUsage>
                            <FlexibleStopUsage>
                                <StopPointRef>{stop_refs[1]}</StopPointRef>
                            </FlexibleStopUsage>
                        </StopPointsInSequence>
                    </FlexibleJourneyPattern>
                </FlexibleService>
            </Service>
        </Services>
    </TransXChange>
    """
    doc = etree.fromstring(xml)
    elements = doc.xpath(
        "//x:Service/x:FlexibleService/x:FlexibleJourneyPattern", namespaces=NAMESPACE
    )

    validator = get_flexible_service_stop_point_ref_validator(db=MagicMock())
    result = validator("", elements)

    assert result == expected
    assert m_stop_point_repo.return_value.get_count.call_count == 1
    assert sorted(
        m_stop_point_repo.return_value.get_count.call_args[1]["atco_codes"]
    ) == sorted(stop_refs)
    assert (
        m_stop_point_repo.return_value.get_count.call_args[1]["bus_stop_type"] == "FLX"
    )
    assert m_stop_point_repo.return_value.get_count.call_args[1]["stop_type"] == "BCT"


@pytest.mark.parametrize(
    ("stop_point_refs", "compliant_count", "expected"),
    [
        pytest.param(
            ["270002700155", "270002700156"],
            2,
            True,
            id="All Stop Points Are Compliant",
        ),
        pytest.param(
            ["270002700156", "270002700157"],
            1,
            False,
            id="One Stop Point Is Non Compliant",
        ),
        pytest.param(
            ["270002700157", "270002700158"],
            0,
            False,
            id="No Stop Points Are Compliant",
        ),
    ],
)
def test_check_flexible_service_stop_points(
    m_stop_point_repo: MagicMock,
    stop_point_refs: list[str],
    compliant_count: int,
    expected: bool,
):
    """
    Service Sto Points Test
    """
    m_stop_point_repo.return_value.get_count.return_value = compliant_count

    xml = f"""
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" SchemaVersion="2.4">
        <Services>
            <Service>
                <FlexibleService>
                    <FlexibleJourneyPattern id="jp_1">
                        <StopPointsInSequence>
                            <FlexibleStopUsage>
                                <StopPointRef>{stop_point_refs[0]}</StopPointRef>
                            </FlexibleStopUsage>
                            <FlexibleStopUsage>
                                <StopPointRef>{stop_point_refs[1]}</StopPointRef>
                            </FlexibleStopUsage>
                        </StopPointsInSequence>
                    </FlexibleJourneyPattern>
                </FlexibleService>
            </Service>
        </Services>
    </TransXChange>
    """
    doc = etree.fromstring(xml)
    elements = doc.xpath(
        "//x:Service/x:FlexibleService/x:FlexibleJourneyPattern", namespaces=NAMESPACE
    )

    validator = get_flexible_service_stop_point_ref_validator(db=MagicMock())
    result = validator("", elements)

    assert result == expected
    assert m_stop_point_repo.return_value.get_count.call_count == 1
    assert sorted(
        m_stop_point_repo.return_value.get_count.call_args[1]["atco_codes"]
    ) == sorted(stop_point_refs)
    assert (
        m_stop_point_repo.return_value.get_count.call_args[1]["bus_stop_type"] == "FLX"
    )
    assert m_stop_point_repo.return_value.get_count.call_args[1]["stop_type"] == "BCT"


@pytest.mark.parametrize(
    ("service_classification", "flexible", "expected"),
    [
        pytest.param(True, True, True, id="Has Service Classification With Flexible"),
        pytest.param(
            True, False, False, id="Has Service Classification Without Flexible"
        ),
        pytest.param(False, False, False, id="No Service Classification"),
    ],
)
def test_has_flexible_service_classification(
    service_classification: bool, flexible: bool, expected: bool
):
    """
    Service Clasification test
    """
    flexible_xml = """<Flexible/>""" if flexible else ""
    classification_xml = (
        f"""<ServiceClassification>{flexible_xml}</ServiceClassification>"""
        if service_classification
        else ""
    )

    xml = f"""
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" SchemaVersion="2.4">
        <Services>
            <Service>
                {classification_xml}
                <FlexibleService>
                    <FlexibleJourneyPattern id="jp_1">
                        <BookingArrangements>
                            <Description>Booking office hours: Mon-Fri 8:30-18:30, Sat 9-17</Description>
                            <Phone><TelNationalNumber>0345 234 3344</TelNationalNumber></Phone>
                            <AllBookingsTaken>true</AllBookingsTaken>
                        </BookingArrangements>
                    </FlexibleJourneyPattern>
                </FlexibleService>
            </Service>
        </Services>
    </TransXChange>
    """
    doc = etree.fromstring(xml)
    elements = doc.xpath("//x:Service", namespaces=NAMESPACE)
    actual = has_flexible_service_classification("", elements)
    assert actual == expected


def test_check_flexible_service_times():
    """
    Flexible Service Times Check test
    """
    xml = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" SchemaVersion="2.4">
        <VehicleJourneys>
            <FlexibleVehicleJourney>
                <DestinationDisplay>Flexible</DestinationDisplay>
                <Direction>outbound</Direction>
                <Description>Monday to Friday service around Market Rasen</Description>
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
        </VehicleJourneys>
    </TransXChange>
    """
    doc = etree.fromstring(xml)
    elements = doc.xpath("//x:VehicleJourneys", namespaces=NAMESPACE)
    actual = check_flexible_service_times("", elements)
    assert actual is True


def test_check_no_flexible_service_times():
    """
    Test no flexible service times
    """
    vehicle_journeys = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
        <VehicleJourneys>
            <VehicleJourney>
                <OperatorRef>tkt_oid</OperatorRef>
                <Operational>
                    <TicketMachine>
                    <JourneyCode>1094</JourneyCode>
                    </TicketMachine>
                </Operational>
                <VehicleJourneyCode>vj_1</VehicleJourneyCode>
                <ServiceRef>PB0002032:468</ServiceRef>
                <LineRef>CALC:PB0002032:468:550</LineRef>
                <JourneyPatternRef>jp_1</JourneyPatternRef>
                <DepartureTime>15:10:00</DepartureTime>
            </VehicleJourney>
            <FlexibleVehicleJourney>
                <DestinationDisplay>Flexible</DestinationDisplay>
                <Direction>outbound</Direction>
                <Description>Monday to Friday service around Market Rasen</Description>
                <VehicleJourneyCode>vj_1</VehicleJourneyCode>
                <ServiceRef>PB0002032:467</ServiceRef>
                <LineRef>ARBB:PB0002032:467:53M</LineRef>
                <JourneyPatternRef>jp_1</JourneyPatternRef>
            </FlexibleVehicleJourney>
        </VehicleJourneys>
    </TransXChange>
    """

    doc = etree.fromstring(vehicle_journeys)
    elements = doc.xpath("//x:VehicleJourneys", namespaces=NAMESPACE)
    actual = check_flexible_service_times("", elements)
    assert actual is False
