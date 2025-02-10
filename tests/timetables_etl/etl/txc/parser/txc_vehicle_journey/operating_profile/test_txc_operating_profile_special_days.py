"""
Test Parsing Special Days Operations
"""

from datetime import date

import pytest
from common_layer.txc.models import TXCDateRange, TXCSpecialDaysOperation
from common_layer.txc.parser.operating_profile import (
    parse_date_range,
    parse_date_ranges,
    parse_special_days_operation,
)
from lxml import etree


@pytest.mark.parametrize(
    "xml_string, is_operation, expected_result",
    [
        pytest.param(
            """
            <SpecialDaysOperation>
                <DaysOfOperation>
                    <DateRange>
                        <StartDate>2023-01-01</StartDate>
                        <EndDate>2023-01-05</EndDate>
                    </DateRange>
                    <DateRange>
                        <StartDate>2023-02-01</StartDate>
                        <EndDate>2023-02-05</EndDate>
                    </DateRange>
                </DaysOfOperation>
                <DaysOfNonOperation>
                    <DateRange>
                        <StartDate>2023-03-01</StartDate>
                        <EndDate>2023-03-05</EndDate>
                    </DateRange>
                </DaysOfNonOperation>
            </SpecialDaysOperation>
            """,
            True,
            [
                TXCDateRange(StartDate=date(2023, 1, 1), EndDate=date(2023, 1, 5)),
                TXCDateRange(StartDate=date(2023, 2, 1), EndDate=date(2023, 2, 5)),
            ],
            id="Valid days of operation",
        ),
        pytest.param(
            """
            <SpecialDaysOperation>
                <DaysOfOperation>
                    <DateRange>
                        <StartDate>2023-01-01</StartDate>
                        <EndDate>2023-01-05</EndDate>
                    </DateRange>
                </DaysOfOperation>
                <DaysOfNonOperation>
                    <DateRange>
                        <StartDate>2023-03-01</StartDate>
                        <EndDate>2023-03-05</EndDate>
                    </DateRange>
                    <DateRange>
                        <StartDate>2023-04-01</StartDate>
                        <EndDate>2023-04-05</EndDate>
                    </DateRange>
                </DaysOfNonOperation>
            </SpecialDaysOperation>
            """,
            False,
            [
                TXCDateRange(StartDate=date(2023, 3, 1), EndDate=date(2023, 3, 5)),
                TXCDateRange(StartDate=date(2023, 4, 1), EndDate=date(2023, 4, 5)),
            ],
            id="Valid days of non-operation",
        ),
    ],
)
def test_parse_date_ranges(
    xml_string: str, is_operation: bool, expected_result: list[TXCDateRange]
):
    """
    Ensure Date Ranges are parsed correctly
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_date_ranges(xml_element, is_operation)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string",
    [
        pytest.param(
            """
            <DateRange>
                <StartDate>2023-01-01</StartDate>
            </DateRange>
            """,
            id="Missing end date",
        ),
        pytest.param(
            """
            <DateRange>
                <EndDate>2023-01-05</EndDate>
            </DateRange>
            """,
            id="Missing start date",
        ),
        pytest.param(
            """
            <DateRange>
            </DateRange>
            """,
            id="Empty date range",
        ),
        pytest.param(
            """
            <DateRange>
                <StartDate></StartDate>
                <EndDate>2023-01-05</EndDate>
            </DateRange>
            """,
            id="Empty start date",
        ),
        pytest.param(
            """
            <DateRange>
                <StartDate>2023-01-01</StartDate>
                <EndDate></EndDate>
            </DateRange>
            """,
            id="Empty end date",
        ),
    ],
)
def test_parse_date_range_returns_none(xml_string: str):
    """
    Test cases where parse_date_range should return None
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_date_range(xml_element)
    assert result is None


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <SpecialDaysOperation>
                <DaysOfOperation>
                    <DateRange>
                        <StartDate>2023-01-01</StartDate>
                        <EndDate>2023-01-05</EndDate>
                    </DateRange>
                </DaysOfOperation>
                <DaysOfNonOperation>
                    <DateRange>
                        <StartDate>2023-03-01</StartDate>
                        <EndDate>2023-03-05</EndDate>
                    </DateRange>
                </DaysOfNonOperation>
            </SpecialDaysOperation>
            """,
            TXCSpecialDaysOperation(
                DaysOfOperation=[
                    TXCDateRange(StartDate=date(2023, 1, 1), EndDate=date(2023, 1, 5))
                ],
                DaysOfNonOperation=[
                    TXCDateRange(StartDate=date(2023, 3, 1), EndDate=date(2023, 3, 5))
                ],
            ),
            id="Valid special days operation",
        ),
        pytest.param(
            """
            <SpecialDaysOperation>
            </SpecialDaysOperation>
            """,
            None,
            id="Empty special days operation",
        ),
    ],
)
def test_parse_special_days_operation(
    xml_string: str, expected_result: TXCSpecialDaysOperation | None
):
    """
    Special Days Operations
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_special_days_operation(xml_element)
    assert result == expected_result
