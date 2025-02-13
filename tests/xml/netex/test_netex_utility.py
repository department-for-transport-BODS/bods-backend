"""
Test Helper Functions
"""

from datetime import UTC, datetime, timedelta, timezone

import pytest
from common_layer.xml.netex.parser import parse_timestamp
from lxml.etree import fromstring


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """<Timestamp>2024-02-14T15:30:00Z</Timestamp>""",
            datetime(2024, 2, 14, 15, 30, 0, tzinfo=UTC),
            id="Valid UTC timestamp",
        ),
        pytest.param(
            """<FromDate>2023-12-31T23:59:59Z</FromDate>""",
            datetime(2023, 12, 31, 23, 59, 59, tzinfo=UTC),
            id="Valid timestamp at year boundary",
        ),
        pytest.param(
            """<Timestamp></Timestamp>""",
            None,
            id="Empty timestamp element",
        ),
        pytest.param(
            """<Timestamp />""",
            None,
            id="Self-closing empty timestamp element",
        ),
        pytest.param(
            """<Timestamp>2024-02-14T15:30:00+00:00</Timestamp>""",
            datetime(2024, 2, 14, 15, 30, 0, tzinfo=UTC),
            id="Valid ISO format with explicit UTC offset",
        ),
        pytest.param(
            """<Timestamp>2024-02-14T16:30:00+01:00</Timestamp>""",
            datetime(2024, 2, 14, 16, 30, 0, tzinfo=timezone(timedelta(hours=1))),
            id="Central European Time (CET)",
        ),
        pytest.param(
            """<Timestamp>2024-02-14T17:30:00+02:00</Timestamp>""",
            datetime(2024, 2, 14, 17, 30, 0, tzinfo=timezone(timedelta(hours=2))),
            id="Eastern European Time (EET)",
        ),
    ],
)
def test_parse_timestamp(xml_string: str, expected_result: datetime | None):
    """
    Test timestamp parsing for various formats and edge cases
    """
    xml_element = fromstring(xml_string)
    result = parse_timestamp(xml_element)
    assert result == expected_result
