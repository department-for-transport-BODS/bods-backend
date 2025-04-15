"""
PTI Base Validator Tests
"""

from unittest.mock import MagicMock, patch

import pytest
from lxml import etree
from pti.app.constants import NAMESPACE
from pti.app.models.models_pti import VehicleJourney
from pti.app.validators.base import BaseValidator


@pytest.fixture(name="m_root")
def mocked_root() -> MagicMock:
    """
    Mock an XML root element with namespaces and xpath methods.
    """
    root = MagicMock()
    root.nsmap = {None: "http://www.example.com"}
    root.xpath = MagicMock()
    return root


def test_lines_property(m_root: MagicMock) -> None:
    validator = BaseValidator(m_root)
    mock_line = MagicMock()
    m_root.xpath.return_value = [mock_line]

    mock_line_obj = MagicMock()
    with patch("pti.app.models.models_pti.Line.from_xml", return_value=mock_line_obj):
        lines = validator.lines

    assert len(lines) == 1
    assert lines[0] is mock_line_obj
    m_root.xpath.assert_called_once_with("//x:Line", namespaces=NAMESPACE)


def test_vehicle_journeys_property(m_root: MagicMock) -> None:
    validator = BaseValidator(m_root)

    # Mock the XML elements returned by root.xpath
    mock_vehicle_journey_xml = MagicMock()
    m_root.xpath.return_value = [mock_vehicle_journey_xml]

    vehicle_journey = VehicleJourney(
        code="Code1",
        line_ref="Line1",
        journey_pattern_ref="Pattern1",
        vehicle_journey_ref="",
        service_ref="Service1",
    )
    with patch(
        "pti.app.models.models_pti.VehicleJourney.from_xml",
        return_value=vehicle_journey,
    ):
        validator = BaseValidator(m_root)
        vehicle_journeys = validator.vehicle_journeys

    assert vehicle_journeys == [
        vehicle_journey
    ], "property returns the correct parsed objects"
    m_root.xpath.assert_called_once_with(
        "//x:VehicleJourneys/x:VehicleJourney", namespaces=NAMESPACE
    )


def test_journey_patterns_property() -> None:
    xml_content = """
    <Root xmlns="http://www.example.com">
        <JourneyPatterns>
            <JourneyPattern id="Pattern1" />
            <JourneyPattern id="Pattern2" />
        </JourneyPatterns>
    </Root>
    """

    root = etree.fromstring(xml_content)
    validator = BaseValidator(root)

    journey_patterns = validator.journey_patterns

    assert len(journey_patterns) == 2, "Expected two journey patterns"
    assert (
        journey_patterns[0].attrib["id"] == "Pattern1"
    ), "First journey pattern ID mismatch"
    assert (
        journey_patterns[1].attrib["id"] == "Pattern2"
    ), "Second journey pattern ID mismatch"


def test_get_journey_pattern_ref_by_vehicle_journey_code(m_root: MagicMock):
    validator = BaseValidator(m_root)
    code = "Code1"
    expected_pattern = "Pattern1"

    vehicle_journies_from_xpath = [MagicMock(), MagicMock()]
    m_root.xpath.return_value = vehicle_journies_from_xpath

    vehicle_journey_1 = MagicMock(
        journey_pattern_ref=expected_pattern, vehicle_journey_ref="", code=code
    )
    vehicle_journey_2 = MagicMock(
        journey_pattern_ref="Pattern2", vehicle_journey_ref="", code="Code2"
    )

    with patch(
        "pti.app.models.models_pti.VehicleJourney.from_xml",
        side_effect=[vehicle_journey_1, vehicle_journey_2],
    ):
        pattern_ref = validator.get_journey_pattern_ref_by_vehicle_journey_code(code)

    assert pattern_ref == expected_pattern


def test_get_journey_pattern_refs_by_line_ref(m_root: MagicMock):
    validator = BaseValidator(m_root)
    m_root.xpath.return_value = [MagicMock(), MagicMock(), MagicMock()]

    m_vehicle_journey_1 = MagicMock(
        line_ref="Line1", code="Code1", journey_pattern_ref="Pattern1"
    )
    m_vehicle_journey_2 = MagicMock(
        line_ref="Line1", code="Code2", journey_pattern_ref="Pattern2"
    )
    m_vehicle_journey_3 = MagicMock(
        line_ref="Line2", code="Code3", journey_pattern_ref="Pattern3"
    )

    line = "Line1"
    expected_pattern_refs = ["Pattern1", "Pattern2"]

    with patch(
        "pti.app.models.models_pti.VehicleJourney.from_xml",
        side_effect=[m_vehicle_journey_1, m_vehicle_journey_2, m_vehicle_journey_3],
    ):
        pattern_refs = validator.get_journey_pattern_refs_by_line_ref(line)

    assert set(pattern_refs) == set(expected_pattern_refs)


def test_get_service_by_vehicle_journey(m_root: MagicMock):
    validator = BaseValidator(m_root)

    # Mock services returned by XPath
    m_service_1 = MagicMock()
    m_service_2 = MagicMock()
    m_root.xpath.return_value = [m_service_1, m_service_2]

    # Mock the ServiceCode returned by XPath calls on individual services
    m_service_1.xpath.return_value = "Service1"
    m_service_2.xpath.return_value = "Service2"

    service_ref = "Service1"
    expected_service = m_service_1

    service = validator.get_service_by_vehicle_journey(service_ref)

    assert service == expected_service


def test_get_stop_point_ref_from_journey_pattern_ref(m_root: MagicMock):
    validator = BaseValidator(m_root)

    section_refs = ["Section1", "Section2"]
    stop_refs_section_1 = ["StopPointRef1", "StopPointRef2"]
    stop_refs_section_2 = ["StopPointRef3", "StopPointRef4"]

    m_root.xpath.side_effect = [
        section_refs,  # First call: JourneyPatternSectionRefs
        stop_refs_section_1,  # Second call: StopPointRefs for Section1
        stop_refs_section_2,  # Second call: StopPointRefs for Section2
    ]

    pattern_ref = "Pattern1"
    expected_stop_refs = [
        "StopPointRef1",
        "StopPointRef2",
        "StopPointRef3",
        "StopPointRef4",
    ]

    stop_refs = validator.get_stop_point_ref_from_journey_pattern_ref(pattern_ref)

    assert set(stop_refs) == set(expected_stop_refs)
    m_root.xpath.assert_any_call(
        "//x:StandardService/x:JourneyPattern[@id='Pattern1']/x:JourneyPatternSectionRefs/text()",
        namespaces=NAMESPACE,
    )
    m_root.xpath.assert_any_call(
        "//x:JourneyPatternSections/x:JourneyPatternSection[@id='Section1']"
        "/x:JourneyPatternTimingLink/*[local-name() = 'From' or local-name() = 'To']/x:StopPointRef/text()",
        namespaces=NAMESPACE,
    )
    m_root.xpath.assert_any_call(
        "//x:JourneyPatternSections/x:JourneyPatternSection[@id='Section2']"
        "/x:JourneyPatternTimingLink/*[local-name() = 'From' or local-name() = 'To']/x:StopPointRef/text()",
        namespaces=NAMESPACE,
    )


@pytest.mark.parametrize(
    "ref, xml_content, expected_section_refs",
    [
        pytest.param(
            "RouteLink1",
            """
            <JourneyPatternSections xmlns="http://www.transxchange.org.uk/">
                <JourneyPatternSection id="Section1">
                    <JourneyPatternTimingLink>
                        <RouteLinkRef>RouteLink1</RouteLinkRef>
                    </JourneyPatternTimingLink>
                </JourneyPatternSection>
            </JourneyPatternSections>
            """,
            ["Section1"],
            id="Single matching section ref",
        ),
        pytest.param(
            "RouteLink2",
            """
            <JourneyPatternSections xmlns="http://www.transxchange.org.uk/">
                <JourneyPatternSection id="Section2">
                    <JourneyPatternTimingLink>
                        <RouteLinkRef>RouteLink2</RouteLinkRef>
                    </JourneyPatternTimingLink>
                </JourneyPatternSection>
                <JourneyPatternSection id="Section3">
                    <JourneyPatternTimingLink>
                        <RouteLinkRef>RouteLink2</RouteLinkRef>
                    </JourneyPatternTimingLink>
                </JourneyPatternSection>
            </JourneyPatternSections>
            """,
            ["Section2", "Section3"],
            id="Multiple matching section refs",
        ),
        pytest.param(
            "RouteLink3",
            """
            <JourneyPatternSections xmlns="http://www.transxchange.org.uk/">
                <JourneyPatternSection id="Section4">
                    <JourneyPatternTimingLink>
                        <RouteLinkRef>RouteLink1</RouteLinkRef>
                    </JourneyPatternTimingLink>
                </JourneyPatternSection>
            </JourneyPatternSections>
            """,
            [],
            id="No matching section refs",
        ),
    ],
)
def test_get_journey_pattern_section_refs_by_route_link_ref(
    ref: str, xml_content: str, expected_section_refs: list[str]
) -> None:
    """
    Test the `get_journey_pattern_section_refs_by_route_link_ref` method with various cases.
    """
    # Parse the XML content
    root = etree.fromstring(xml_content)

    # Create the validator
    validator = BaseValidator(root)

    # Call the method
    section_refs = validator.get_journey_pattern_section_refs_by_route_link_ref(ref)

    # Assert the result
    assert set(section_refs) == set(expected_section_refs)
