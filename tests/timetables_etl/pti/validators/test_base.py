"""
PTI Base Validator Tests
"""

from unittest.mock import MagicMock, patch

import pytest
from lxml import etree
from pti.app.models.models_pti import VehicleJourney
from pti.app.validators.base import BaseValidator


@pytest.fixture(name="m_root")
def mocked_root():
    """
    Mock an XML root element with namespaces and xpath methods.
    """
    root = MagicMock()
    root.nsmap = {None: "http://www.example.com"}
    root.xpath = MagicMock()
    return root


def test_lines_property(m_root):
    validator = BaseValidator(m_root)
    mock_line = MagicMock()
    m_root.xpath.return_value = [mock_line]

    mock_line_obj = MagicMock()
    with patch("pti.app.models.models_pti.Line.from_xml", return_value=mock_line_obj):
        lines = validator.lines

    assert len(lines) == 1
    assert lines[0] is mock_line_obj
    m_root.xpath.assert_called_once_with("//x:Line", namespaces=validator.namespaces)


def test_vehicle_journeys_property(m_root):
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
        "//x:VehicleJourneys/x:VehicleJourney", namespaces=validator.namespaces
    )


def test_journey_patterns_property():
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


def test_get_journey_pattern_ref_by_vehicle_journey_code(m_root):
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


def test_get_journey_pattern_refs_by_line_ref(m_root):
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


def test_get_service_by_vehicle_journey(m_root):
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


def test_index_jp_sections(m_root):
    """
    Test _index_jp_sections method by mocking journey pattern section elements
    """
    validator = BaseValidator(m_root)

    section1 = MagicMock()
    section1.get.return_value = "Section1"
    section1.xpath.return_value = ["StopPointRef1", "StopPointRef2"]

    section2 = MagicMock()
    section2.get.return_value = "Section2"
    section2.xpath.return_value = ["StopPointRef3", "StopPointRef4"]

    m_root.xpath.return_value = [section1, section2]

    result = validator._index_jp_sections()

    expected = {
        "Section1": ["StopPointRef1", "StopPointRef2"],
        "Section2": ["StopPointRef3", "StopPointRef4"],
    }

    assert result == expected
    m_root.xpath.assert_called_once_with(
        "//x:JourneyPatternSections/x:JourneyPatternSection",
        namespaces=validator.namespaces,
    )
    section1.xpath.assert_called_once_with(
        "./x:JourneyPatternTimingLink/*[local-name()='From' or local-name()='To']/x:StopPointRef/text()",
        namespaces=validator.namespaces,
    )
    section2.xpath.assert_called_once_with(
        "./x:JourneyPatternTimingLink/*[local-name()='From' or local-name()='To']/x:StopPointRef/text()",
        namespaces=validator.namespaces,
    )


def test_index_journey_patterns(m_root):
    """
    Test _index_journey_patterns method by mocking journey pattern elements.
    """
    validator = BaseValidator(m_root)

    jp1 = MagicMock()
    jp1.get.return_value = "Pattern1"
    jp1.xpath.return_value = ["Section1", "Section2"]

    jp2 = MagicMock()
    jp2.get.return_value = "Pattern2"
    jp2.xpath.return_value = ["Section3"]

    m_root.xpath.return_value = [jp1, jp2]

    result = validator._index_journey_patterns()

    expected = {
        "Pattern1": ["Section1", "Section2"],
        "Pattern2": ["Section3"],
    }

    assert result == expected
    m_root.xpath.assert_called_once_with(
        "//x:StandardService/x:JourneyPattern",
        namespaces=validator.namespaces,
    )
    jp1.xpath.assert_called_once_with(
        "./x:JourneyPatternSectionRefs/text()", namespaces=validator.namespaces
    )
    jp2.xpath.assert_called_once_with(
        "./x:JourneyPatternSectionRefs/text()", namespaces=validator.namespaces
    )


def test_get_stop_point_ref_from_journey_pattern_ref_lazy_indexes(m_root):
    """
    Test get_stop_point_ref_from_journey_pattern_ref builds indexes lazily
    and returns correct unique stop point refs.
    """
    validator = BaseValidator(m_root)

    # Patch the indexing methods to return mocked data and track calls
    with patch.object(
        validator,
        "_index_jp_sections",
        return_value={
            "Section1": ["StopPointRef2", "StopPointRef1"],
            "Section2": ["StopPointRef4", "StopPointRef3"],
        },
    ) as mock_index_sections, patch.object(
        validator,
        "_index_journey_patterns",
        return_value={
            "Pattern1": ["Section1", "Section2"],
        },
    ) as mock_index_patterns:

        pattern_ref = "Pattern1"
        expected_stop_refs = [
            "StopPointRef1",
            "StopPointRef2",
            "StopPointRef3",
            "StopPointRef4",
        ]

        # Call the method under test, which should trigger _build_indexes and caching
        stop_refs_first_call = validator.get_stop_point_ref_from_journey_pattern_ref(
            pattern_ref
        )
        stop_refs_second_call = validator.get_stop_point_ref_from_journey_pattern_ref(
            pattern_ref
        )

        # Verify result correctness
        assert set(stop_refs_first_call) == set(expected_stop_refs)
        assert set(stop_refs_second_call) == set(expected_stop_refs)

        # The indexing methods should be called only once despite multiple calls
        mock_index_sections.assert_called_once()
        mock_index_patterns.assert_called_once()

        # Also verify the internal _indexes cache is populated
        assert validator._indexes is not None
        assert "section_to_stop_refs" in validator._indexes
        assert "jp_to_section_refs" in validator._indexes


@pytest.mark.parametrize(
    "ref, xml_content, expected_section_refs",
    [
        pytest.param(
            "RouteLink1",
            """
            <JourneyPatternSections xmlns="http://www.example.com">
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
            <JourneyPatternSections xmlns="http://www.example.com">
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
            <JourneyPatternSections xmlns="http://www.example.com">
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
    ref, xml_content, expected_section_refs
):
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
