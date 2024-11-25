"""
XML Parsing Types Functions Tests
"""

from datetime import datetime, timezone

import pytest
from lxml import etree

from timetables_etl.etl.app.txc.parser.utils_attributes import (
    parse_xml_attribute,
    parse_xml_datetime,
    parse_xml_int,
)


@pytest.mark.parametrize(
    "xml_string, attribute_name, expected",
    [
        ("<tag></tag>", "attribute", None),
        ("<tag attribute=''>attribute</tag>", "attribute", None),
        ("<tag attribute='value'>attribute</tag>", "attribute", "value"),
        ("<tag other='value'>attribute</tag>", "attribute", None),
    ],
    ids=["No Attributes", "Empty String", "Valid Attribute", "Non-existent Attribute"],
)
def test_parse_xml_attribute(xml_string, attribute_name, expected):
    """
    Test function use dto extract strings from XML attribute
    """
    root = etree.fromstring(xml_string)
    assert parse_xml_attribute(root, attribute_name) == expected


@pytest.mark.parametrize(
    "xml_string, attribute_name, expected",
    [
        ("<tag></tag>", "attribute", None),
        ("<tag attribute=''>attribute</tag>", "attribute", None),
        ("<tag attribute='invalid_int'>attribute</tag>", "attribute", None),
        ("<tag attribute='42'>attribute</tag>", "attribute", 42),
    ],
    ids=["No Attributes", "Empty String", "Not a Number", "Valid Number"],
)
def test_parse_xml_int(xml_string, attribute_name, expected):
    """
    Test Parsing an XML Attribute Int
    """
    root = etree.fromstring(xml_string)
    assert parse_xml_int(root, attribute_name) == expected


@pytest.mark.parametrize(
    "xml_string, attribute_name, expected",
    [
        ("<tag></tag>", "attribute", None),
        ("<tag attribute=''>attribute</tag>", "attribute", None),
        ("<tag attribute='invalid_date'>attribute</tag>", "attribute", None),
        (
            "<tag attribute='2023-05-15T10:30:00+00:00'>attribute</tag>",
            "attribute",
            datetime(2023, 5, 15, 10, 30, tzinfo=timezone.utc),
        ),
    ],
    ids=["No Attributes", "Empty String", "Invalid Date", "Valid Date"],
)
def test_parse_xml_datetime(xml_string, attribute_name, expected):
    """
    Datetime parsing tests
    """
    root = etree.fromstring(xml_string)
    assert parse_xml_datetime(root, attribute_name) == expected
