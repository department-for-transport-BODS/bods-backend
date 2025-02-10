"""
XML parser helpers
"""

from datetime import datetime, timezone

import pytest
from common_layer.xml.utils import (
    parse_creation_datetime,
    parse_modification,
    parse_modification_datetime,
    parse_revision_number,
)
from lxml import etree


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        pytest.param("<tag></tag>", None, id="No Attributes"),
        pytest.param(
            "<tag CreationDateTime=''>CreationDateTime</tag>", None, id="Empty String"
        ),
        pytest.param(
            "<tag CreationDateTime='invalid_date'>CreationDateTime</tag>",
            None,
            id="Invalid Date",
        ),
        pytest.param(
            "<tag CreationDateTime='2023-05-15T10:30:00+00:00'>CreationDateTime</tag>",
            datetime(2023, 5, 15, 10, 30, tzinfo=timezone.utc),
            id="Valid Date",
        ),
    ],
)
def test_parse_creation_datetime(xml_string: str, expected: datetime | None):
    """
    Parse CreationDateTime on a attribute
    """
    root = etree.fromstring(xml_string)
    assert parse_creation_datetime(root) == expected


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        pytest.param("<tag></tag>", None, id="No Attributes"),
        pytest.param(
            "<tag ModificationDateTime=''>ModificationDateTime</tag>",
            None,
            id="Empty String",
        ),
        pytest.param(
            "<tag ModificationDateTime='invalid_date'>ModificationDateTime</tag>",
            None,
            id="Invalid Date",
        ),
        pytest.param(
            "<tag ModificationDateTime='2023-05-15T10:30:00+00:00'>ModificationDateTime</tag>",
            datetime(2023, 5, 15, 10, 30, tzinfo=timezone.utc),
            id="Valid Date",
        ),
    ],
)
def test_parse_modification_datetime(xml_string: str, expected: datetime | None):
    """
    Test that modificationdatetime attribute is parsed correctly
    """
    root = etree.fromstring(xml_string)
    assert parse_modification_datetime(root) == expected


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        pytest.param("<tag></tag>", None, id="No Attributes"),
        pytest.param(
            "<tag RevisionNumber=''>RevisionNumber</tag>", None, id="Empty String"
        ),
        pytest.param(
            "<tag RevisionNumber='invalid_int'>RevisionNumber</tag>",
            None,
            id="Not a number",
        ),
        pytest.param(
            "<tag RevisionNumber='42'>RevisionNumber</tag>", 42, id="Correctly Parsing"
        ),
    ],
)
def test_parse_revision_number(xml_string: str, expected: int | None):
    """
    Test extracting the Revision Number
    """
    root = etree.fromstring(xml_string)
    assert parse_revision_number(root) == expected


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        pytest.param("<tag></tag>", None, id="No Attributes"),
        pytest.param(
            "<tag Modification=''>Modification</tag>", None, id="Empty String"
        ),
        pytest.param(
            "<tag Modification='revise'>Modification</tag>",
            "revise",
            id="Valid Modification",
        ),
        pytest.param(
            "<tag other='value'>Modification</tag>", None, id="Non-existent Attribute"
        ),
    ],
)
def test_parse_modification(xml_string: str, expected: str):
    """
    Parse the Modification data
    """
    root = etree.fromstring(xml_string)
    assert parse_modification(root) == expected
