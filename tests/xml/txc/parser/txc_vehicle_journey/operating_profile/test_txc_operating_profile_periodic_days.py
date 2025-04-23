"""
Test PeriodicDayType Parsing
"""

import pytest
from common_layer.xml.txc.models import TXCPeriodicDayType
from common_layer.xml.txc.parser.operating_profile import parse_periodic_days
from lxml import etree


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <PeriodicDayType>
                <WeekOfMonth>
                    <WeekNumber>first</WeekNumber>
                </WeekOfMonth>
                <WeekOfMonth>
                    <WeekNumber>third</WeekNumber>
                </WeekOfMonth>
            </PeriodicDayType>
            """,
            TXCPeriodicDayType(first=True, third=True),
            id="Valid periodic days (first and third weeks)",
        ),
        pytest.param(
            """
            <PeriodicDayType>
                <WeekOfMonth>
                    <WeekNumber>second</WeekNumber>
                </WeekOfMonth>
                <WeekOfMonth>
                    <WeekNumber>fourth</WeekNumber>
                </WeekOfMonth>
                <WeekOfMonth>
                    <WeekNumber>last</WeekNumber>
                </WeekOfMonth>
            </PeriodicDayType>
            """,
            TXCPeriodicDayType(second=True, forth=True, last=True),
            id="Valid periodic days (second, fourth, and last weeks)",
        ),
        pytest.param(
            """
            <PeriodicDayType>
            </PeriodicDayType>
            """,
            TXCPeriodicDayType(),
            id="Empty periodic days",
        ),
    ],
)
def test_parse_periodic_days(
    xml_string: str, expected_result: TXCPeriodicDayType
) -> None:
    """
    Periodic dats parsing
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_periodic_days(xml_element)
    assert result == expected_result
