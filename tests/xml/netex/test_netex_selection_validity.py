"""
Selection Validity Tests
"""

from datetime import UTC, datetime

import pytest
from common_layer.xml.netex.models import (
    AvailabilityCondition,
    SelectionValidityConditions,
)
from common_layer.xml.netex.parser import (
    parse_availability_condition,
    parse_selection_validity_conditions,
)
from lxml import etree

from tests.xml.conftest import assert_model_equal


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <AvailabilityCondition version="1.0" id="r1">
                <FromDate>2019-08-14T00:00:00Z</FromDate>
                <ToDate>2024-08-14T00:00:00Z</ToDate>
            </AvailabilityCondition>
            """,
            AvailabilityCondition(
                version="1.0",
                id="r1",
                FromDate=datetime(2019, 8, 14, 0, 0, tzinfo=UTC),
                ToDate=datetime(2024, 8, 14, 0, 0, tzinfo=UTC),
            ),
            id="Valid availability condition with both dates",
        ),
        pytest.param(
            """
            <AvailabilityCondition version="1.0" id="r1">
                <FromDate>2019-08-14T00:00:00Z</FromDate>
            </AvailabilityCondition>
            """,
            AvailabilityCondition(
                version="1.0",
                id="r1",
                FromDate=datetime(2019, 8, 14, 0, 0, tzinfo=UTC),
                ToDate=None,
            ),
            id="Valid availability condition with only FromDate",
        ),
        pytest.param(
            """
            <AvailabilityCondition id="r1">
                <FromDate>2019-08-14T00:00:00Z</FromDate>
            </AvailabilityCondition>
            """,
            AvailabilityCondition(
                version="1.0",
                id="r1",
                FromDate=datetime(2019, 8, 14, 0, 0, tzinfo=UTC),
                ToDate=None,
            ),
            id="Valid availability condition with default version",
        ),
        pytest.param(
            """
            <AvailabilityCondition version="1.0" id="r1">
                <FromDate></FromDate>
                <ToDate>2024-08-14T00:00:00Z</ToDate>
            </AvailabilityCondition>
            """,
            AvailabilityCondition(
                version="1.0",
                id="r1",
                FromDate=None,
                ToDate=datetime(2024, 8, 14, 0, 0, tzinfo=UTC),
            ),
            id="Valid availability condition with empty FromDate",
        ),
        pytest.param(
            """
            <AvailabilityCondition version="1.0">
                <FromDate>2019-08-14T00:00:00Z</FromDate>
            </AvailabilityCondition>
            """,
            AvailabilityCondition(
                version="1.0",
                id="",
                FromDate=datetime(2019, 8, 14, 0, 0, tzinfo=UTC),
                ToDate=None,
            ),
            id="Valid availability condition with missing id",
        ),
    ],
)
def test_parse_availability_condition(
    xml_string: str, expected_result: AvailabilityCondition
):
    """
    Test AvailabilityCondition parsing
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_availability_condition(xml_element)
    assert_model_equal(result, expected_result)


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <selectionValidityConditions>
                <AvailabilityCondition version="1.0" id="r1">
                    <FromDate>2019-08-14T00:00:00Z</FromDate>
                </AvailabilityCondition>
            </selectionValidityConditions>
            """,
            SelectionValidityConditions(
                AvailabilityConditions=[
                    AvailabilityCondition(
                        version="1.0",
                        id="r1",
                        FromDate=datetime(2019, 8, 14, 0, 0, tzinfo=UTC),
                        ToDate=None,
                    )
                ],
                SimpleAvailabilityConditions=[],
            ),
            id="Single availability condition with FromDate only",
        ),
        pytest.param(
            """
            <selectionValidityConditions>
                <AvailabilityCondition version="1.0" id="r1">
                    <FromDate>2019-08-14T00:00:00Z</FromDate>
                    <ToDate>2024-08-14T00:00:00Z</ToDate>
                </AvailabilityCondition>
                <AvailabilityCondition version="1.0" id="r2">
                    <FromDate>2024-08-15T00:00:00Z</FromDate>
                    <ToDate>2025-08-14T00:00:00Z</ToDate>
                </AvailabilityCondition>
            </selectionValidityConditions>
            """,
            SelectionValidityConditions(
                AvailabilityConditions=[
                    AvailabilityCondition(
                        version="1.0",
                        id="r1",
                        FromDate=datetime(2019, 8, 14, 0, 0, tzinfo=UTC),
                        ToDate=datetime(2024, 8, 14, 0, 0, tzinfo=UTC),
                    ),
                    AvailabilityCondition(
                        version="1.0",
                        id="r2",
                        FromDate=datetime(2024, 8, 15, 0, 0, tzinfo=UTC),
                        ToDate=datetime(2025, 8, 14, 0, 0, tzinfo=UTC),
                    ),
                ],
                SimpleAvailabilityConditions=[],
            ),
            id="Multiple availability conditions",
        ),
        pytest.param(
            """
            <selectionValidityConditions>
                <SimpleAvailabilityCondition>
                    <FromDate>2019-08-14T00:00:00Z</FromDate>
                </SimpleAvailabilityCondition>
            </selectionValidityConditions>
            """,
            SelectionValidityConditions(
                AvailabilityConditions=[],
                SimpleAvailabilityConditions=[],
            ),
            id="Simple availability condition (not implemented)",
        ),
        pytest.param(
            """
            <selectionValidityConditions>
                <UnknownTag>Some content</UnknownTag>
            </selectionValidityConditions>
            """,
            SelectionValidityConditions(
                AvailabilityConditions=[],
                SimpleAvailabilityConditions=[],
            ),
            id="Unknown tag",
        ),
        pytest.param(
            """
            <selectionValidityConditions>
            </selectionValidityConditions>
            """,
            SelectionValidityConditions(
                AvailabilityConditions=[],
                SimpleAvailabilityConditions=[],
            ),
            id="Empty conditions",
        ),
    ],
)
def test_parse_selection_validity_conditions(
    xml_str: str, expected: SelectionValidityConditions
) -> None:
    """Test parsing of selection validity conditions with various inputs."""
    elem = etree.fromstring(xml_str.strip())
    result = parse_selection_validity_conditions(elem)
    assert_model_equal(result, expected)
