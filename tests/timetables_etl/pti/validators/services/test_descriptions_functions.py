"""
Test Descriptions Service Functions
"""

from typing import Callable

import pytest
from lxml import etree
from lxml.etree import _Element  # type: ignore
from pti.app.constants import NAMESPACE
from pti.app.validators.service.descriptions import (
    check_description_for_inbound_description,
    check_description_for_outbound_description,
    check_inbound_outbound_description,
)


@pytest.mark.parametrize(
    ("xml_content", "function", "expected"),
    [
        pytest.param(
            """
            <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" SchemaVersion="2.4">
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
            """,
            check_inbound_outbound_description,
            False,
            id="No inbound or outbound description",
        ),
        pytest.param(
            """
            <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" SchemaVersion="2.4">
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
            """,
            check_inbound_outbound_description,
            True,
            id="Both inbound and outbound descriptions",
        ),
        pytest.param(
            """
            <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" SchemaVersion="2.4">
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
            """,
            check_inbound_outbound_description,
            True,
            id="Only inbound description",
        ),
        pytest.param(
            """
            <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" SchemaVersion="2.4">
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
            """,
            check_inbound_outbound_description,
            True,
            id="Only outbound description",
        ),
        pytest.param(
            """
            <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" SchemaVersion="2.4">
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
            """,
            check_description_for_inbound_description,
            True,
            id="Valid inbound description with description element",
        ),
        pytest.param(
            """
            <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" SchemaVersion="2.4">
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
            """,
            check_description_for_inbound_description,
            False,
            id="Invalid inbound description missing description element",
        ),
        pytest.param(
            """
            <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" SchemaVersion="2.4">
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
            """,
            check_description_for_outbound_description,
            True,
            id="Valid outbound description with description element",
        ),
        pytest.param(
            """
            <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" SchemaVersion="2.4">
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
            """,
            check_description_for_outbound_description,
            False,
            id="Invalid outbound description missing description element",
        ),
    ],
)
def test_service_description_validators(
    xml_content: str,
    function: Callable[[_Element | None, list[_Element]], bool],
    expected: bool,
) -> None:
    """
    Test service description validators with various XML configurations.
    """
    doc = etree.fromstring(xml_content)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = function(None, elements)
    assert actual == expected
