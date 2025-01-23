"""
Tests for XML Handling Utils
"""

from unittest.mock import Mock

import pytest
from dateutil import parser
from lxml import etree
from lxml.etree import Element
from pti.app.utils.utils_xml import (
    cast_to_bool,
    cast_to_date,
    contains_date,
    extract_text,
    has_name,
    has_prohibited_chars,
    is_member_of,
    regex,
    strip,
)


@pytest.mark.parametrize(
    "elements, default, expected",
    [
        pytest.param(
            [Mock(spec=Element, text="test")], None, "test", id="List Element"
        ),
        pytest.param(["test"], None, "test", id="List String"),
        pytest.param(
            Mock(spec=Element, text="test"), None, "test", id="Single Element"
        ),
        pytest.param("test", None, "test", id="String"),
        pytest.param(
            Mock(spec=Element), "default", "default", id="Empty Element With Default"
        ),
        pytest.param([], "default", "default", id="Empty List With Default"),
    ],
)
def test_extract_text(
    elements,
    default: str | None,
    expected: str | None,
):
    """
    Test extraction of text content from various element types
    Validates proper text extraction from elements, strings and lists with defaults
    """
    actual = extract_text(elements, default)
    assert actual == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        pytest.param([Mock(spec=Element, text="true")], True, id="List Element True"),
        pytest.param(
            [Mock(spec=Element, text="false")], False, id="List Element False"
        ),
        pytest.param(Mock(spec=Element, text="true"), True, id="Single Element True"),
        pytest.param(
            Mock(spec=Element, text="false"), False, id="Single Element False"
        ),
        pytest.param(["true"], True, id="List String True"),
        pytest.param(["false"], False, id="List String False"),
        pytest.param("true", True, id="String True"),
        pytest.param("false", False, id="String False"),
        pytest.param(Mock(spec=Element), False, id="Empty Element"),
    ],
)
def test_cast_to_bool(value, expected: bool):
    """
    Test casting various XML element and string inputs to boolean values
    Validates that true/false text content is properly converted
    """
    context = Mock()
    actual = cast_to_bool(context, value)
    assert actual == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        pytest.param(
            [Mock(spec=Element, text="2015-01-01")],
            parser.parse("2015-01-01").timestamp(),
            id="List Element Date",
        ),
        pytest.param(
            Mock(spec=Element, text="2015-01-01"),
            parser.parse("2015-01-01").timestamp(),
            id="Single Element Date",
        ),
        pytest.param(
            "2015-01-01", parser.parse("2015-01-01").timestamp(), id="String Date"
        ),
    ],
)
def test_cast_to_date(value, expected: float):
    """
    Test casting XML date elements to timestamp
    Validates proper parsing of date strings in various formats
    """
    context = Mock()
    actual = cast_to_date(context, value)
    assert actual == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        pytest.param(
            [Mock(spec=Element, text="world")], False, id="List Element No Date"
        ),
        pytest.param(
            [Mock(spec=Element, text="2020-12-01 world")],
            True,
            id="List Element With Date",
        ),
        pytest.param(
            Mock(spec=Element, text="hello,world"), False, id="Single Element No Date"
        ),
        pytest.param(
            Mock(spec=Element, text="12-01 world"), True, id="Single Element With Date"
        ),
        pytest.param(["hello,world"], False, id="List String No Date"),
        pytest.param(["01/08/21 hello world"], True, id="List String With Date"),
        pytest.param("hello,world", False, id="String No Date"),
        pytest.param("01/08/21 hello world", True, id="String With Date"),
        pytest.param("15 hello world", False, id="String With Number"),
        pytest.param(Mock(spec=Element), False, id="Empty Element"),
    ],
)
def test_contains_date(value, expected: bool):
    """
    Test detection of date strings in element text content
    Validates identification of various date formats while ignoring plain numbers
    """
    context = Mock()
    actual = contains_date(context, value)
    assert actual == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        pytest.param(
            [Mock(spec=Element, text="hello,world")],
            True,
            id="List Element With Prohibited Chars",
        ),
        pytest.param(
            [Mock(spec=Element, text="hello world")],
            False,
            id="List Element Without Prohibited Chars",
        ),
        pytest.param(
            Mock(spec=Element, text="hello,world"),
            True,
            id="Single Element With Prohibited Chars",
        ),
        pytest.param(
            Mock(spec=Element, text="false"),
            False,
            id="Single Element Without Prohibited Chars",
        ),
        pytest.param(["hello,world"], True, id="List String With Prohibited Chars"),
        pytest.param(["false"], False, id="List String Without Prohibited Chars"),
        pytest.param("hello,world", True, id="String With Prohibited Chars"),
        pytest.param("false", False, id="String Without Prohibited Chars"),
        pytest.param(Mock(spec=Element), False, id="Empty Element"),
    ],
)
def test_has_prohibited_chars(value, expected: bool):
    """
    Test detection of prohibited characters in element text content
    Validates identification of disallowed XML characters like commas, brackets, etc.
    """
    context = Mock()
    actual = has_prohibited_chars(context, value)
    assert actual == expected


@pytest.mark.parametrize(
    "value, list_items, expected",
    [
        pytest.param(
            [Mock(spec=Element, text="other")],
            ("one", "two"),
            False,
            id="List Element Non-Member",
        ),
        pytest.param(
            [Mock(spec=Element, text="one")],
            ("one", "two"),
            True,
            id="List Element Member",
        ),
        pytest.param(
            Mock(spec=Element, text="other"),
            ("one", "two"),
            False,
            id="Single Element Non-Member",
        ),
        pytest.param(
            Mock(spec=Element, text="one"),
            ("one", "two"),
            True,
            id="Single Element Member",
        ),
        pytest.param("other", ("one", "two"), False, id="String Non-Member"),
        pytest.param("one", ("one", "two"), True, id="String Member"),
        pytest.param("", ("one", "two"), False, id="Empty String"),
        pytest.param(Mock(spec=Element), ("one", "two"), False, id="Empty Element"),
    ],
)
def test_is_member_of(
    value,
    list_items: tuple[str, ...],
    expected: bool,
):
    """
    Test membership checking of element text content against a list of values
    Validates that text content is properly checked against allowed values
    """
    context = Mock()
    actual = is_member_of(context, value, *list_items)
    assert actual == expected


@pytest.mark.parametrize(
    "element, pattern, expected",
    [
        pytest.param(
            Mock(spec=Element, text="abc123"),
            r"[a-z]+\d+",
            True,
            id="Valid Pattern Match",
        ),
        pytest.param(
            Mock(spec=Element, text="ABC"), r"[a-z]+", False, id="Invalid Pattern Match"
        ),
        pytest.param(Mock(spec=Element), r"[a-z]+", False, id="Empty Element"),
    ],
)
def test_regex(element, pattern: str, expected: bool):
    """
    Test regex pattern matching against element text content
    Validates that text properly matches against provided patterns
    """
    context = Mock()
    actual = regex(context, element, pattern)
    assert actual == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        pytest.param(
            Mock(spec=Element, text="  test  "), "test", id="Element With Whitespace"
        ),
        pytest.param("  test  ", "test", id="String With Whitespace"),
        pytest.param(Mock(spec=Element), "", id="Empty Element"),
        pytest.param("", "", id="Empty String"),
    ],
)
def test_strip(text, expected: str):
    """
    Test stripping whitespace from element text content
    Validates proper removal of leading and trailing whitespace
    """
    context = Mock()
    actual = strip(context, text)
    assert actual == expected


@pytest.mark.parametrize(
    "xml_input, names, expected",
    [
        pytest.param(
            "<root><Sunday /><Monday /></root>",
            ["Sunday", "Monday"],
            True,
            id="Multiple Elements All Match",
        ),
        pytest.param(
            "<root><Sunday /></root>",
            ["Monday", "Tuesday"],
            False,
            id="Single Element No Match",
        ),
        pytest.param(
            "<root><Sunday /><Monday /><Tuesday /></root>",
            ["Sunday", "Monday"],
            False,
            id="Some Elements Match But Not All",
        ),
        pytest.param(
            "<root><Sunday xmlns='http://test.com'/></root>",
            ["Sunday"],
            True,
            id="Element With Namespace",
        ),
        pytest.param("<root/>", ["Sunday"], True, id="Empty Element List"),
    ],
)
def test_has_name(xml_input: str, names: list[str], expected: bool):
    """
    Test validation of XML element names against provided patterns.
    Tests various scenarios including multiple elements, namespaces, and empty cases.
    """
    context = Mock()
    doc = etree.fromstring(xml_input.encode("utf-8"))
    elements = list(doc)
    actual = has_name(context, elements, *names)
    assert actual is expected
