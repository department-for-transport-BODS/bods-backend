"""
Test Service Functions
"""

import pytest
from lxml import etree
from pti.app.constants import NAMESPACE
from pti.app.validators.service.service import (
    check_service_group_validations,
    has_flexible_or_standard_service,
)


@pytest.mark.parametrize(
    ("flexible_classification", "flexible_service", "standard_service", "expected"),
    [
        pytest.param(
            True,
            True,
            True,
            True,
            id="Has Flexible Classification And Flexible Service And Standard Service",
        ),
        pytest.param(
            True,
            True,
            False,
            True,
            id="Has Flexible Classification And Flexible Service Only",
        ),
        pytest.param(
            True,
            False,
            True,
            False,
            id="Has Flexible Classification And Standard Service Only",
        ),
        pytest.param(True, False, False, False, id="Has Flexible Classification Only"),
        pytest.param(False, False, True, True, id="Has Standard Service Only"),
        pytest.param(False, False, False, False, id="Has No Services"),
    ],
)
def test_has_flexible_or_standard_service(
    flexible_classification: bool,
    flexible_service: bool,
    standard_service: bool,
    expected: bool,
):
    """
    Test Flexible or Standard Service Checking
    """

    flexible_classification_xml = """
        <ServiceClassification>
            <Flexible/>
        </ServiceClassification>
    """

    flexible_service_xml = """
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

    standard_service_xml = """
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

    service_template = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" SchemaVersion="2.4">
        <Services>
            <Service>
                {classification}
                {flexible}
                {standard}
            </Service>
        </Services>
    </TransXChange>
    """

    xml = service_template.format(
        classification=flexible_classification_xml if flexible_classification else "",
        flexible=flexible_service_xml if flexible_service else "",
        standard=standard_service_xml if standard_service else "",
    )

    doc = etree.fromstring(xml)
    elements = doc.xpath("//x:Service", namespaces=NAMESPACE)
    actual = has_flexible_or_standard_service(None, elements)
    assert actual == expected


@pytest.mark.parametrize(
    "services_xml, expected",
    [
        pytest.param(
            """
            <Service>
                <ServiceCode>UZ000KBUS:11</ServiceCode>
                <StandardService></StandardService>
            </Service>
            <Service>
                <ServiceClassification>
                    <Flexible/>
                </ServiceClassification>
                <ServiceCode>PF0000459:134</ServiceCode>
            </Service>
        """,
            True,
            id="Flexible and Standard Services",
        ),
        pytest.param(
            """
            <Service>
                <ServiceClassification>
                    <Flexible/>
                </ServiceClassification>
                <ServiceCode>UZ000KBUS:11</ServiceCode>
            </Service>
        """,
            True,
            id="Unregistered Flexible Service",
        ),
        pytest.param(
            """
            <Service>
                <ServiceClassification>
                    <Flexible/>
                </ServiceClassification>
                <ServiceCode>PF0000459:134</ServiceCode>
            </Service>
        """,
            True,
            id="Registered Flexible Service",
        ),
        pytest.param(
            """
            <Service>
                <ServiceCode>PF0000459:134</ServiceCode>
                <StandardService></StandardService>
            </Service>
        """,
            True,
            id="Registered Standard Service",
        ),
        pytest.param(
            """
            <Service>
                <ServiceCode>UZ000KBUS:11</ServiceCode>
                <StandardService></StandardService>
            </Service>
        """,
            True,
            id="Unregistered Standard Service",
        ),
        pytest.param(
            """
            <Service>
                <ServiceCode>PF0000459:134</ServiceCode>
                <StandardService></StandardService>
            </Service>
            <Service>
                <ServiceCode>PF0000559:135</ServiceCode>
                <StandardService></StandardService>
            </Service>
        """,
            False,
            id="Two Registered Standard Services",
        ),
        pytest.param(
            """
            <Service>
                <ServiceCode>UZ000KBUS:11</ServiceCode>
                <StandardService></StandardService>
            </Service>
            <Service>
                <ServiceCode>PF0000559:135</ServiceCode>
                <StandardService></StandardService>
            </Service>
        """,
            False,
            id="Registered and Unregistered StandardServices",
        ),
        pytest.param(
            """
            <Service>
                <ServiceClassification>
                    <Flexible/>
                </ServiceClassification>
                <ServiceCode>PF0000459:134</ServiceCode>
            </Service>
            <Service>
                <ServiceCode>PF0000559:135</ServiceCode>
                <StandardService></StandardService>
            </Service>
        """,
            False,
            id="Registered Standard and Flexible Services",
        ),
    ],
)
def test_check_service_group_validations(services_xml: str, expected: bool) -> None:
    """
    Test Validating Services Groups of Standard or Flexible Services
    """
    xml = f"""
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" SchemaVersion="2.4">
        <Services>
            {services_xml}
        </Services>
    </TransXChange>
    """

    doc = etree.fromstring(xml)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = check_service_group_validations(None, elements)
    assert actual == expected
