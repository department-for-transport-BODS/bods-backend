"""
XML Parsing Types Functions Tests
"""

from datetime import datetime, timezone

import pytest
from common_layer.xml.utils import (
    parse_xml_attribute,
    parse_xml_datetime,
    parse_xml_int,
)
from lxml import etree


@pytest.mark.parametrize(
    "xml_string, attribute_name, expected",
    [
        pytest.param("<tag></tag>", "attribute", None, id="No Attributes"),
        pytest.param(
            "<tag attribute=''>attribute</tag>", "attribute", None, id="Empty String"
        ),
        pytest.param(
            "<tag attribute='value'>attribute</tag>",
            "attribute",
            "value",
            id="Valid Attribute",
        ),
        pytest.param(
            "<tag other='value'>attribute</tag>",
            "attribute",
            None,
            id="Non-existent Attribute",
        ),
    ],
)
def test_parse_xml_attribute(
    xml_string: str, attribute_name: str, expected: str | None
):
    """
    Test function use dto extract strings from XML attribute
    """
    root = etree.fromstring(xml_string)
    assert parse_xml_attribute(root, attribute_name) == expected


@pytest.mark.parametrize(
    "xml_string, attribute_name, expected",
    [
        pytest.param("<tag></tag>", "attribute", None, id="No Attributes"),
        pytest.param(
            "<tag attribute=''>attribute</tag>", "attribute", None, id="Empty String"
        ),
        pytest.param(
            "<tag attribute='invalid_int'>attribute</tag>",
            "attribute",
            None,
            id="Not a Number",
        ),
        pytest.param(
            "<tag attribute='42'>attribute</tag>", "attribute", 42, id="Valid Number"
        ),
    ],
)
def test_parse_xml_int(xml_string: str, attribute_name: str, expected: int | None):
    """
    Test Parsing an XML Attribute Int
    """
    root = etree.fromstring(xml_string)
    assert parse_xml_int(root, attribute_name) == expected


@pytest.mark.parametrize(
    "xml_string, attribute_name, expected",
    [
        pytest.param("<tag></tag>", "attribute", None, id="No Attributes"),
        pytest.param(
            "<tag attribute=''>attribute</tag>", "attribute", None, id="Empty String"
        ),
        pytest.param(
            "<tag attribute='invalid_date'>attribute</tag>",
            "attribute",
            None,
            id="Invalid Date",
        ),
        pytest.param(
            "<tag attribute='2023-05-15T10:30:00+00:00'>attribute</tag>",
            "attribute",
            datetime(2023, 5, 15, 10, 30, tzinfo=timezone.utc),
            id="Valid Date",
        ),
    ],
)
def test_parse_xml_datetime(
    xml_string: str, attribute_name: str, expected: datetime | None
):
    """
    Datetime parsing tests
    """
    root = etree.fromstring(xml_string)
    assert parse_xml_datetime(root, attribute_name) == expected
