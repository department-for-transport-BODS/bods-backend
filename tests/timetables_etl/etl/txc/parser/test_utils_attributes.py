"""
XML parser helpers
"""

from datetime import datetime, timezone

import pytest
from lxml import etree

from timetables_etl.etl.app.txc.parser.utils_attributes import (
    parse_creation_datetime,
    parse_modification,
    parse_modification_datetime,
    parse_revision_number,
)


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        ("<tag></tag>", None),
        ("<tag CreationDateTime=''>CreationDateTime</tag>", None),
        ("<tag CreationDateTime='invalid_date'>CreationDateTime</tag>", None),
        (
            "<tag CreationDateTime='2023-05-15T10:30:00+00:00'>CreationDateTime</tag>",
            datetime(2023, 5, 15, 10, 30, tzinfo=timezone.utc),
        ),
    ],
    ids=["No Attributes", "Empty String", "Invalid Date", "Valid Date"],
)
def test_parse_creation_datetime(xml_string, expected):
    """
    Parse CreationDateTime on a attribute
    """
    root = etree.fromstring(xml_string)
    assert parse_creation_datetime(root) == expected


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        ("<tag></tag>", None),
        ("<tag ModificationDateTime=''>ModificationDateTime</tag>", None),
        ("<tag ModificationDateTime='invalid_date'>ModificationDateTime</tag>", None),
        (
            "<tag ModificationDateTime='2023-05-15T10:30:00+00:00'>ModificationDateTime</tag>",
            datetime(2023, 5, 15, 10, 30, tzinfo=timezone.utc),
        ),
    ],
    ids=["No Attributes", "Empty String", "Invalid Date", "Valid Date"],
)
def test_parse_modification_datetime(xml_string, expected):
    """
    Test that modificationdatetime attribute is parsed correctly
    """
    root = etree.fromstring(xml_string)
    assert parse_modification_datetime(root) == expected


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        ("<tag></tag>", None),
        ("<tag RevisionNumber=''>RevisionNumber</tag>", None),
        ("<tag RevisionNumber='invalid_int'>RevisionNumber</tag>", None),
        ("<tag RevisionNumber='42'>RevisionNumber</tag>", 42),
    ],
    ids=["No Attributes", "Empty String", "Not a number", "Correctly Parsing"],
)
def test_parse_revision_number(xml_string, expected):
    """
    Test extracting the Revision Number
    """
    root = etree.fromstring(xml_string)
    assert parse_revision_number(root) == expected


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        ("<tag></tag>", None),
        ("<tag Modification=''>Modification</tag>", None),
        ("<tag Modification='revise'>Modification</tag>", "revise"),
        ("<tag other='value'>Modification</tag>", None),
    ],
    ids=[
        "No Attributes",
        "Empty String",
        "Valid Modification",
        "Non-existent Attribute",
    ],
)
def test_parse_modification(xml_string, expected):
    """
    Parse the Modification data
    """
    root = etree.fromstring(xml_string)
    assert parse_modification(root) == expected
