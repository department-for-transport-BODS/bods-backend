"""
Test Descriptions Service Functions
"""

from lxml import etree
from pti.app.validators.service.descriptions import (
    check_description_for_inbound_description,
    check_description_for_outbound_description,
    check_inbound_outbound_description,
)


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
