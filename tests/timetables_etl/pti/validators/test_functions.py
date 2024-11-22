from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
from dateutil import parser
from freezegun import freeze_time
from lxml import etree
from lxml.etree import Element
from pti.validators.functions import (
    cast_to_bool,
    cast_to_date,
    check_description_for_inbound_description,
    check_description_for_outbound_description,
    check_flexible_service_times,
    check_flexible_service_timing_status,
    check_inbound_outbound_description,
    check_service_group_validations,
    contains_date,
    has_flexible_or_standard_service,
    has_flexible_service_classification,
    has_name,
    has_prohibited_chars,
    is_member_of,
    today,
    validate_licence_number,
    validate_modification_date_time,
)

from tests.timetables_etl.pti.validators.constants import TXC_END, TXC_START

DATA_DIR = Path(__file__).parent / "data"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ([Mock(spec=Element, text="true")], True),
        ([Mock(spec=Element, text="false")], False),
        (Mock(spec=Element, text="true"), True),
        (Mock(spec=Element, text="false"), False),
        (["true"], True),
        (["false"], False),
        ("true", True),
        ("false", False),
        (Mock(spec=Element), False),
    ],
)
def test_cast_to_bool(value, expected):
    context = Mock()
    actual = cast_to_bool(context, value)
    assert actual == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            [Mock(spec=Element, text="2015-01-01")],
            parser.parse("2015-01-01").timestamp(),
        ),
        (
            Mock(spec=Element, text="2015-01-01"),
            parser.parse("2015-01-01").timestamp(),
        ),
        ("2015-01-01", parser.parse("2015-01-01").timestamp()),
    ],
)
def test_cast_to_date(value, expected):
    context = Mock()
    actual = cast_to_date(context, value)
    assert actual == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ([Mock(spec=Element, text="world")], False),
        ([Mock(spec=Element, text="2020-12-01 world")], True),
        (Mock(spec=Element, text="hello,world"), False),
        (Mock(spec=Element, text="12-01 world"), True),
        (["hello,world"], False),
        (["01/08/21 hello world"], True),
        ("hello,world", False),
        ("01/08/21 hello world", True),
        ("15 hello world", False),
        (Mock(spec=Element), False),
    ],
)
def test_contains_date(value, expected):
    context = Mock()
    actual = contains_date(context, value)
    assert actual == expected


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (["otherPoint", "otherPoint", "otherPoint"], True),
        (["otherPoint", "TXT", "otherPoint"], False),
        (["", "", ""], False),
        (["XYZ", "ABC", ""], False),
    ],
)
def test_check_flexible_service_timing_status(values, expected):
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    timing_status = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
        <Services>
            <Service>
                <FlexibleService>
                    <FlexibleJourneyPattern id="jp_1">
                        <StopPointsInSequence>
                            <FixedStopUsage SequenceNumber="1">
                                <StopPointRef>0600000102</StopPointRef>
                                <TimingStatus>{0}</TimingStatus>
                            </FixedStopUsage>
                            <FixedStopUsage SequenceNumber="2">
                                <StopPointRef>0600000101</StopPointRef>
                                <TimingStatus>{1}</TimingStatus>
                            </FixedStopUsage>
                            <FlexibleStopUsage>
                                <StopPointRef>270002700155</StopPointRef>
                            </FlexibleStopUsage>
                            <FixedStopUsage SequenceNumber="4">
                                <StopPointRef>0600000103</StopPointRef>
                                <TimingStatus>{2}</TimingStatus>
                            </FixedStopUsage>
                        </StopPointsInSequence>
                    </FlexibleJourneyPattern>
                </FlexibleService>
            </Service>
        </Services>
    </TransXChange>
    """
    string_xml = timing_status.format(*values)
    doc = etree.fromstring(string_xml)
    elements = doc.xpath("//x:Service/x:FlexibleService/x:FlexibleJourneyPattern", namespaces=NAMESPACE)
    actual = check_flexible_service_timing_status("", elements)
    assert actual == expected


def test_check_flexible_service_times():
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
                <FlexibleServiceTimes>
                    <ServicePeriod>
                        <StartTime>07:00:00</StartTime>
                        <EndTime>19:00:00</EndTime>
                    </ServicePeriod>
                </FlexibleServiceTimes>
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

    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    doc = etree.fromstring(vehicle_journeys)
    elements = doc.xpath("//x:VehicleJourneys", namespaces=NAMESPACE)
    actual = check_flexible_service_times("", elements)
    assert actual == True


def test_check_no_flexible_service_times():
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

    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    doc = etree.fromstring(vehicle_journeys)
    elements = doc.xpath("//x:VehicleJourneys", namespaces=NAMESPACE)
    actual = check_flexible_service_times("", elements)
    assert actual == False


def test_check_no_inbound_outbound_description():
    services = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
    <Services>
        <Service>
            <ServiceClassification>
                <Flexible/>
            </ServiceClassification>
        </Service>
        <Service>
            <Lines>
                <Line id="ARBB:UZ000WBCT:B1081:123">
                    <LineName>123</LineName>
                </Line>
            </Lines>
            <StandardService>
                <Origin>Putteridge High School</Origin>
                <Destination>Church Street</Destination>
                <JourneyPattern id="jp_3">
                <DestinationDisplay>Church Street</DestinationDisplay>
                <OperatorRef>tkt_oid</OperatorRef>
                <Direction>inbound</Direction>
                <RouteRef>rt_0000</RouteRef>
                <JourneyPatternSectionRefs>js_1</JourneyPatternSectionRefs>
                </JourneyPattern>
            </StandardService>
        </Service>
    </Services>
    </TransXChange>
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    doc = etree.fromstring(services)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = check_inbound_outbound_description("", elements)
    assert actual == False


def test_check_inbound_outbound_description():
    services = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
    <Services>
        <Service>
            <ServiceClassification>
                <Flexible/>
            </ServiceClassification>
        </Service>
        <Service>
            <Lines>
                <Line id="ARBB:UZ000WBCT:B1081:123">
                    <LineName>123</LineName>
                    <OutboundDescription>
                        <Description>Putteridge High School to Church Street</Description>
                    </OutboundDescription>
                    <InboundDescription>
                        <Description>Church Street to Putteridge High School</Description>
                    </InboundDescription>
                </Line>
            </Lines>
            <StandardService>
                <Origin>Putteridge High School</Origin>
                <Destination>Church Street</Destination>
                <JourneyPattern id="jp_3">
                <DestinationDisplay>Church Street</DestinationDisplay>
                <OperatorRef>tkt_oid</OperatorRef>
                <Direction>inbound</Direction>
                <RouteRef>rt_0000</RouteRef>
                <JourneyPatternSectionRefs>js_1</JourneyPatternSectionRefs>
                </JourneyPattern>
            </StandardService>
        </Service>
    </Services>
    </TransXChange>
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    doc = etree.fromstring(services)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = check_inbound_outbound_description("", elements)
    assert actual == True


def test_check_description_for_inbound_description():
    services = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
    <Services>
        <Service>
            <ServiceClassification>
                <Flexible/>
            </ServiceClassification>
        </Service>
        <Service>
            <Lines>
                <Line id="ARBB:UZ000WBCT:B1081:123">
                    <LineName>123</LineName>
                    <InboundDescription>
                        <Origin>Langley Park</Origin>
                        <Destination>Street</Destination>
                        <Vias>
                            <Via>Chester</Via>
                            <Via>le</Via>
                        </Vias>
                        <Description>Church Street to Putteridge High School</Description>
                    </InboundDescription>
                </Line>
            </Lines>
            <StandardService>
                <Origin>Putteridge High School</Origin>
                <Destination>Church Street</Destination>
                <JourneyPattern id="jp_3">
                <DestinationDisplay>Church Street</DestinationDisplay>
                <OperatorRef>tkt_oid</OperatorRef>
                <Direction>inbound</Direction>
                <RouteRef>rt_0000</RouteRef>
                <JourneyPatternSectionRefs>js_1</JourneyPatternSectionRefs>
                </JourneyPattern>
            </StandardService>
        </Service>
    </Services>
    </TransXChange>
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    doc = etree.fromstring(services)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = check_description_for_inbound_description("", elements)
    assert actual == True


def test_check_description_for_inbound_description_failed():
    services = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
    <Services>
        <Service>
            <ServiceClassification>
                <Flexible/>
            </ServiceClassification>
        </Service>
        <Service>
            <Lines>
                <Line id="ARBB:UZ000WBCT:B1081:123">
                    <LineName>123</LineName>
                    <InboundDescription>
                        <Origin>Langley Park</Origin>
                        <Destination>Street</Destination>
                        <Vias>
                            <Via>Chester</Via>
                            <Via>le</Via>
                        </Vias>
                    </InboundDescription>
                </Line>
            </Lines>
            <StandardService>
                <Origin>Putteridge High School</Origin>
                <Destination>Church Street</Destination>
                <JourneyPattern id="jp_3">
                <DestinationDisplay>Church Street</DestinationDisplay>
                <OperatorRef>tkt_oid</OperatorRef>
                <Direction>inbound</Direction>
                <RouteRef>rt_0000</RouteRef>
                <JourneyPatternSectionRefs>js_1</JourneyPatternSectionRefs>
                </JourneyPattern>
            </StandardService>
        </Service>
    </Services>
    </TransXChange>
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    doc = etree.fromstring(services)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = check_description_for_inbound_description("", elements)
    assert actual == False


def test_check_description_for_outbound_description():
    services = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
    <Services>
        <Service>
            <ServiceClassification>
                <Flexible/>
            </ServiceClassification>
        </Service>
        <Service>
            <Lines>
                <Line id="ARBB:UZ000WBCT:B1081:123">
                    <LineName>123</LineName>
                    <OutboundDescription>
                        <Origin>Langley Park</Origin>
                        <Destination>Street</Destination>
                        <Vias>
                            <Via>Chester</Via>
                            <Via>le</Via>
                        </Vias>
                        <Description>This is outbound description</Description>
                    </OutboundDescription>
                </Line>
            </Lines>
            <StandardService>
                <Origin>Putteridge High School</Origin>
                <Destination>Church Street</Destination>
                <JourneyPattern id="jp_3">
                <DestinationDisplay>Church Street</DestinationDisplay>
                <OperatorRef>tkt_oid</OperatorRef>
                <Direction>inbound</Direction>
                <RouteRef>rt_0000</RouteRef>
                <JourneyPatternSectionRefs>js_1</JourneyPatternSectionRefs>
                </JourneyPattern>
            </StandardService>
        </Service>
    </Services>
    </TransXChange>
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    doc = etree.fromstring(services)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = check_description_for_outbound_description("", elements)
    assert actual == True


def test_check_description_for_outbound_description_failed():
    services = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
    <Services>
        <Service>
            <ServiceClassification>
                <Flexible/>
            </ServiceClassification>
        </Service>
        <Service>
            <Lines>
                <Line id="ARBB:UZ000WBCT:B1081:123">
                    <LineName>123</LineName>
                    <OutboundDescription>
                        <Origin>Langley Park</Origin>
                        <Destination>Street</Destination>
                        <Vias>
                            <Via>Chester</Via>
                            <Via>le</Via>
                        </Vias>
                    </OutboundDescription>
                </Line>
            </Lines>
            <StandardService>
                <Origin>Putteridge High School</Origin>
                <Destination>Church Street</Destination>
                <JourneyPattern id="jp_3">
                <DestinationDisplay>Church Street</DestinationDisplay>
                <OperatorRef>tkt_oid</OperatorRef>
                <Direction>inbound</Direction>
                <RouteRef>rt_0000</RouteRef>
                <JourneyPatternSectionRefs>js_1</JourneyPatternSectionRefs>
                </JourneyPattern>
            </StandardService>
        </Service>
    </Services>
    </TransXChange>
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    doc = etree.fromstring(services)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = check_description_for_outbound_description("", elements)
    assert actual == False


def test_check_only_inbound_description():
    services = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
    <Services>
        <Service>
            <ServiceClassification>
                <Flexible/>
            </ServiceClassification>
        </Service>
        <Service>
            <Lines>
                <Line id="ARBB:UZ000WBCT:B1081:123">
                    <LineName>123</LineName>
                    <InboundDescription>
                        <Description>Church Street to Putteridge High School</Description>
                    </InboundDescription>
                </Line>
            </Lines>
            <StandardService>
                <Origin>Putteridge High School</Origin>
                <Destination>Church Street</Destination>
                <JourneyPattern id="jp_3">
                <DestinationDisplay>Church Street</DestinationDisplay>
                <OperatorRef>tkt_oid</OperatorRef>
                <Direction>inbound</Direction>
                <RouteRef>rt_0000</RouteRef>
                <JourneyPatternSectionRefs>js_1</JourneyPatternSectionRefs>
                </JourneyPattern>
            </StandardService>
        </Service>
    </Services>
    </TransXChange>
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    doc = etree.fromstring(services)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = check_inbound_outbound_description("", elements)
    assert actual == True


def test_check_only_outbound_description():
    services = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
    <Services>
        <Service>
            <ServiceClassification>
                <Flexible/>
            </ServiceClassification>
        </Service>
        <Service>
            <Lines>
                <Line id="ARBB:UZ000WBCT:B1081:123">
                    <LineName>123</LineName>
                    <OutboundDescription>
                        <Description>Putteridge High School to Church Street</Description>
                    </OutboundDescription>
                </Line>
            </Lines>
            <StandardService>
                <Origin>Putteridge High School</Origin>
                <Destination>Church Street</Destination>
                <JourneyPattern id="jp_3">
                <DestinationDisplay>Church Street</DestinationDisplay>
                <OperatorRef>tkt_oid</OperatorRef>
                <Direction>inbound</Direction>
                <RouteRef>rt_0000</RouteRef>
                <JourneyPatternSectionRefs>js_1</JourneyPatternSectionRefs>
                </JourneyPattern>
            </StandardService>
        </Service>
    </Services>
    </TransXChange>
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    doc = etree.fromstring(services)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = check_inbound_outbound_description("", elements)
    assert actual == True


@pytest.mark.parametrize("args, expected", [(["Sunday", "Monday"], True), (["Monday", "Tuesday"], False)])
def test_has_name(args, expected):
    context = Mock()
    s = TXC_START + "<Sunday />" + TXC_END
    doc = etree.fromstring(s.encode("utf-8"))
    sunday = doc.getchildren()
    actual = has_name(context, sunday, *args)
    assert actual is expected


@pytest.mark.parametrize(
    ("flexible_classification", "flexible_service", "standard_service", "expected"),
    [
        (True, True, True, True),
        (True, True, False, True),
        (True, False, True, False),
        (True, False, False, False),
        (False, False, True, True),
        (False, False, False, False),
    ],
)
def test_has_flexible_or_standard_service(flexible_classification, flexible_service, standard_service, expected):
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    flexible_classification_present = """
        <ServiceClassification>
            <Flexible/>
        </ServiceClassification>
    """
    flexible_service_present = """
        <FlexibleService>
            <FlexibleJourneyPattern id="jp_1">
                <BookingArrangements>
                    <Description>The booking office is open for all advance booking Monday to Friday 8:30am – 6:30pm, Saturday 9am – 5pm</Description>
                    <Phone>
                        <TelNationalNumber>0345 234 3344</TelNationalNumber>
                    </Phone>
                    <AllBookingsTaken>true</AllBookingsTaken>
                </BookingArrangements>
            </FlexibleJourneyPattern>
        </FlexibleService>
    """
    standard_service_present = """
        <StandardService>
            <Origin>Putteridge High School</Origin>
            <Destination>Church Street</Destination>
            <JourneyPattern id="jp_2">
            <DestinationDisplay>Church Street</DestinationDisplay>
            <OperatorRef>tkt_oid</OperatorRef>
            <Direction>inbound</Direction>
            <RouteRef>rt_0000</RouteRef>
            <JourneyPatternSectionRefs>js_1</JourneyPatternSectionRefs>
            </JourneyPattern>
        </StandardService>
    """
    service = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
        <Services>
		    <Service>
                {0}
                {1}
                {2}
            </Service>
        </Services>
    </TransXChange>
    """
    if flexible_classification:
        if flexible_service:
            string_xml = service.format(
                flexible_classification_present,
                flexible_service_present,
                standard_service,
            )
        else:
            string_xml = service.format(flexible_classification_present, "", standard_service)
    else:
        if standard_service:
            string_xml = service.format("", "", standard_service_present)
        else:
            string_xml = service.format("", "", "")

    doc = etree.fromstring(string_xml)
    elements = doc.xpath("//x:Service", namespaces=NAMESPACE)
    actual = has_flexible_or_standard_service("", elements)
    assert actual == expected


@pytest.mark.parametrize(
    ("service_classification", "flexible", "expected"),
    [
        (True, True, True),
        (True, False, False),
        (False, False, False),
    ],
)
def test_has_flexible_service_classification(service_classification, flexible, expected):
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    service_classification_present = """
        <ServiceClassification>
        </ServiceClassification>
    """
    service_classification_flexible_present = """
        <ServiceClassification>
            <Flexible/>
        </ServiceClassification>
    """
    service = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
        <Services>
		    <Service>
                {0}
                <FlexibleService>
                    <FlexibleJourneyPattern id="jp_1">
                        <BookingArrangements>
                            <Description>The booking office is open for all advance booking Monday to Friday 8:30am – 6:30pm, Saturday 9am – 5pm</Description>
                            <Phone>
                                <TelNationalNumber>0345 234 3344</TelNationalNumber>
                            </Phone>
                            <AllBookingsTaken>true</AllBookingsTaken>
                        </BookingArrangements>
                    </FlexibleJourneyPattern>
			    </FlexibleService>
            </Service>
            <Service>
                <StandardService>
                    <Origin>Putteridge High School</Origin>
                    <Destination>Church Street</Destination>
                    <JourneyPattern id="jp_2">
                    <DestinationDisplay>Church Street</DestinationDisplay>
                    <OperatorRef>tkt_oid</OperatorRef>
                    <Direction>inbound</Direction>
                    <RouteRef>rt_0000</RouteRef>
                    <JourneyPatternSectionRefs>js_1</JourneyPatternSectionRefs>
                    </JourneyPattern>
                </StandardService>
            </Service>
        </Services>
    </TransXChange>
    """
    if service_classification:
        if flexible:
            string_xml = service.format(service_classification_flexible_present)
        else:
            string_xml = service.format(service_classification_present)
    else:
        string_xml = service

    doc = etree.fromstring(string_xml)
    elements = doc.xpath("//x:Service", namespaces=NAMESPACE)
    actual = has_flexible_service_classification("", elements)
    assert actual == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ([Mock(spec=Element, text="hello,world")], True),
        ([Mock(spec=Element, text="hello world")], False),
        (Mock(spec=Element, text="hello,world"), True),
        (Mock(spec=Element, text="false"), False),
        (["hello,world"], True),
        (["false"], False),
        ("hello,world", True),
        ("false", False),
        (Mock(spec=Element), False),
    ],
)
def test_has_prohibited_chars(value, expected):
    context = Mock()
    actual = has_prohibited_chars(context, value)
    assert actual == expected


def test_check_service_group_validations_with_flexible_and_standard_services():
    services = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
        <Services>
            <Service>
                <ServiceCode>UZ000KBUS:11</ServiceCode>
                <StandardService>
                </StandardService>
            </Service>
            <Service>
                <ServiceClassification>
				    <Flexible/>
			    </ServiceClassification>
                <ServiceCode>PF0000459:134</ServiceCode>
            </Service>
        </Services>
    </TransXChange>
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}

    doc = etree.fromstring(services)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = check_service_group_validations("", elements)
    assert actual == True


def test_check_service_group_validations_with_unregistered_flexible_service():
    services = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
        <Services>
            <Service>
                <ServiceClassification>
				    <Flexible/>
			    </ServiceClassification>
                <ServiceCode>UZ000KBUS:11</ServiceCode>
            </Service>
        </Services>
    </TransXChange>
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}

    doc = etree.fromstring(services)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = check_service_group_validations("", elements)
    assert actual == True


def test_check_service_group_validations_with_registered_flexible_service():
    services = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
        <Services>
            <Service>
                <ServiceClassification>
				    <Flexible/>
			    </ServiceClassification>
                <ServiceCode>PF0000459:134</ServiceCode>
            </Service>
        </Services>
    </TransXChange>
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}

    doc = etree.fromstring(services)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = check_service_group_validations("", elements)
    assert actual == True


def test_check_service_group_validations_with_registered_standard_services():
    services = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
        <Services>
            <Service>
                <ServiceCode>PF0000459:134</ServiceCode>
                <StandardService>
                </StandardService>
            </Service>
        </Services>
    </TransXChange>
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}

    doc = etree.fromstring(services)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = check_service_group_validations("", elements)
    assert actual == True


def test_check_service_group_validations_with_unregistered_standard_services():
    services = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
        <Services>
            <Service>
                <ServiceCode>UZ000KBUS:11</ServiceCode>
                <StandardService>
                </StandardService>
            </Service>
        </Services>
    </TransXChange>
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}

    doc = etree.fromstring(services)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = check_service_group_validations("", elements)
    assert actual == True


def test_check_service_group_validations_with_two_registered_standard_services():
    services = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
        <Services>
            <Service>
                <ServiceCode>PF0000459:134</ServiceCode>
                <StandardService>
                </StandardService>
            </Service>
            <Service>
                <ServiceCode>PF0000559:135</ServiceCode>
                <StandardService>
                </StandardService>
            </Service>
        </Services>
    </TransXChange>
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}

    doc = etree.fromstring(services)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = check_service_group_validations("", elements)
    assert actual == False


def test_check_service_group_validations_with_registered_standard_and_unregistered_services():
    services = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
        <Services>
            <Service>
                <ServiceCode>UZ000KBUS:11</ServiceCode>
                <StandardService>
                </StandardService>
            </Service>
            <Service>
                <ServiceCode>PF0000559:135</ServiceCode>
                <StandardService>
                </StandardService>
            </Service>
        </Services>
    </TransXChange>
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}

    doc = etree.fromstring(services)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = check_service_group_validations("", elements)
    assert actual == False


def test_check_service_group_validations_with_registered_standard_and_registered_flexible_services():
    services = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
        <Services>
            <Service>
                <ServiceClassification>
				    <Flexible/>
			    </ServiceClassification>
                <ServiceCode>PF0000459:134</ServiceCode>
            </Service>
            <Service>
                <ServiceCode>PF0000559:135</ServiceCode>
                <StandardService>
                </StandardService>
            </Service>
        </Services>
    </TransXChange>
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}

    doc = etree.fromstring(services)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = check_service_group_validations("", elements)
    assert actual == False


@pytest.mark.parametrize(
    ("value", "list_items", "expected"),
    [
        ([Mock(spec=Element, text="other")], ("one", "two"), False),
        ([Mock(spec=Element, text="one")], ("one", "two"), True),
        (Mock(spec=Element, text="other"), ("one", "two"), False),
        (Mock(spec=Element, text="one"), ("one", "two"), True),
        ("other", ("one", "two"), False),
        ("one", ("one", "two"), True),
        ("", ("one", "two"), False),
        (Mock(spec=Element), ("one", "two"), False),
    ],
)
def test_is_member_of(value, list_items, expected):
    context = Mock()
    actual = is_member_of(context, value, *list_items)
    assert actual == expected


@freeze_time("2020-02-02")
def test_today():
    context = Mock()
    actual = today(context)
    assert actual == parser.parse("2020-02-02").timestamp()


def test_validate_licence_number_coach_data():
    """
    This test case validates LicenceNumber is not a mandatory element for Operators with PrimaryMode as Coach
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    string_xml = DATA_DIR / "coaches" / "coach_operator.xml"
    with string_xml.open("r") as txc_xml:
        doc = etree.parse(txc_xml)
        elements = doc.xpath("//x:Operator", namespaces=NAMESPACE)
        actual = validate_licence_number("", elements)
        assert actual == True


def test_validate_licence_number_non_coach_data_success():
    """
    This test case validates LicenceNumber is a mandatory element for Non Coach Operators
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    string_xml = DATA_DIR / "coaches" / "non_coach_data_operator.xml"
    with string_xml.open("r") as txc_xml:
        doc = etree.parse(txc_xml)
        elements = doc.xpath("//x:Operator", namespaces=NAMESPACE)
        actual = validate_licence_number("", elements)
        assert actual == True


def test_validate_licence_number_non_coach_data_failed():
    """
    This test case validates LicenceNumber is a mandatory element for Non Coach Operators
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    string_xml = DATA_DIR / "coaches" / "non_coach_data_operator_without_licence_number.xml"
    with string_xml.open("r") as txc_xml:
        doc = etree.parse(txc_xml)
        elements = doc.xpath("//x:Operator", namespaces=NAMESPACE)
        actual = validate_licence_number("", elements)
        assert actual == False


@pytest.mark.parametrize(
    "attributes, expected_result",
    [
        # Case 1: revision_number = "0" and dates are equal
        ({"RevisionNumber": "0", "ModificationDateTime": "2024-11-14T12:00:00", "CreationDateTime": "2024-11-14T12:00:00"}, True),
        # Case 2: revision_number = "0" and dates are not equal
        ({"RevisionNumber": "0", "ModificationDateTime": "2024-11-14T12:00:00", "CreationDateTime": "2024-11-14T11:00:00"}, False),
        # Case 3: revision_number != "0" and creation_date < modification_date
        ({"RevisionNumber": "1", "ModificationDateTime": "2024-11-14T12:00:00", "CreationDateTime": "2024-11-14T11:00:00"}, True),
        # Case 4: revision_number != "0" and creation_date >= modification_date
        ({"RevisionNumber": "1", "ModificationDateTime": "2024-11-14T12:00:00", "CreationDateTime": "2024-11-14T12:00:00"}, False),
    ],
)
def test_validate_modification_date_time(attributes, expected_result):
    """
    Test the `validate_modification_date_time` function with various cases.
    """
    # Mock the root element with attributes
    mock_root = MagicMock()
    mock_root.attrib = attributes

    # Call the function
    context = MagicMock()  # Assuming context is unused in this function
    result = validate_modification_date_time(context, [mock_root])

    # Assert the result
    assert result == expected_result