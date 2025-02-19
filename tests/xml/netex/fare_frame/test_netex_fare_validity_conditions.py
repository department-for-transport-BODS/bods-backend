"""
Test Validity Conditions
"""

from datetime import datetime

import pytest
from common_layer.xml.netex.models.netex_utility import FromToDate
from common_layer.xml.netex.parser.fare_frame.netex_fare_tariff import (
    parse_validity_conditions,
)

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import parse_xml_str_as_netex


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <validityConditions>
                <ValidBetween>
                    <FromDate>2025-02-05T00:00:00</FromDate>
                    <ToDate>2125-02-05T00:00:00</ToDate>
                </ValidBetween>
                <UnknownTag>Something</UnknownTag>
            </validityConditions>
            """,
            [
                FromToDate(
                    FromDate=datetime(2025, 2, 5, 0, 0),
                    ToDate=datetime(2125, 2, 5, 0, 0),
                )
            ],
            id="Basic validity conditions with unknown tag",
        ),
        pytest.param(
            """
            <validityConditions>
            </validityConditions>
            """,
            [],
            id="Empty validity conditions",
        ),
    ],
)
def test_parse_validity_conditions(xml_str: str, expected: list[FromToDate]) -> None:
    """Test parsing of validity conditions with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_validity_conditions(elem)

    for result_condition, expected_condition in zip(result, expected):
        assert_model_equal(result_condition, expected_condition)
