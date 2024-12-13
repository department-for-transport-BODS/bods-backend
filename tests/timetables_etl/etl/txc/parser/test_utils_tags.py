"""
Test XML Tag Extraction Functions
"""

from datetime import date, datetime

import pytest
from lxml import etree

from timetables_etl.etl.app.txc.parser.utils_tags import (
    does_element_exist,
    get_elem_bool_default,
    get_element_bool,
    get_element_date,
    get_element_datetime,
    get_element_int,
    get_element_text,
    get_element_texts,
)


@pytest.mark.parametrize(
    "xml_string, element_name, expected_result",
    [
        pytest.param(
            "<root><StAndrewsDay/></root>", "StAndrewsDay", True, id="Element exists"
        ),
        pytest.param(
            "<root></root>", "StAndrewsDay", False, id="Element does not exist"
        ),
        pytest.param(
            "<root><OtherElement/></root>",
            "StAndrewsDay",
            False,
            id="Different element exists",
        ),
    ],
)
def test_does_element_exist(xml_string: str, element_name: str, expected_result: bool):
    """
    Tests for Elements that don't have data
    e.g.
    <StAndrewsDay/>
    """
    xml_element = etree.fromstring(xml_string)
    result = does_element_exist(xml_element, element_name)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, field_name, expected",
    [
        pytest.param("<tag></tag>", "element", None, id="No Elements"),
        pytest.param(
            "<tag><element></element></tag>", "element", None, id="Empty Element"
        ),
        pytest.param(
            "<tag><element>value</element></tag>",
            "element",
            "value",
            id="Valid Element Text",
        ),
        pytest.param(
            "<tag><other>value</other></tag>",
            "element",
            None,
            id="Non-existent Element",
        ),
    ],
)
def test_get_element_text(xml_string: str, field_name: str, expected: str | None):
    """
    Get the text data for an element
    """
    root = etree.fromstring(xml_string)
    assert get_element_text(root, field_name) == expected


@pytest.mark.parametrize(
    "xml_string, field_name, expected",
    [
        pytest.param(
            """
            <Root>
                <StopAreas>Area1</StopAreas>
                <StopAreas>Area2</StopAreas>
                <StopAreas>Area3</StopAreas>
            </Root>
            """,
            "StopAreas",
            ["Area1", "Area2", "Area3"],
            id="All Valid",
        ),
        pytest.param(
            """
            <Root>
                <StopAreas></StopAreas>
                <StopAreas>Area2</StopAreas>
                <StopAreas>Area3</StopAreas>
            </Root> 
            """,
            "StopAreas",
            ["Area2", "Area3"],
            id="Ignore Empty Value",
        ),
        pytest.param(
            """
                <Root>
                    <OtherTag>Value</OtherTag>
                </Root>
                """,
            "StopAreas",
            [],
            id="Not Found",
        ),
    ],
)
def test_get_element_texts(xml_string: str, field_name: str, expected: list[str]):
    """
    Get the text data for an element
    """
    root = etree.fromstring(xml_string)
    assert get_element_texts(root, field_name) == expected


@pytest.mark.parametrize(
    "xml_string, field_name, expected",
    [
        pytest.param("<tag></tag>", "element", None, id="No Elements"),
        pytest.param(
            "<tag><element></element></tag>", "element", None, id="Empty Element"
        ),
        pytest.param(
            "<tag><element>value</element></tag>",
            "element",
            None,
            id="Non-numeric Element",
        ),
        pytest.param(
            "<tag><element>42</element></tag>",
            "element",
            42,
            id="Valid Numeric Element",
        ),
    ],
)
def test_get_element_int(xml_string: str, field_name: str, expected: int | None):
    """
    Test getting and converting element text to an int
    """
    root = etree.fromstring(xml_string)
    assert get_element_int(root, field_name) == expected


@pytest.mark.parametrize(
    "xml_string, field_name, expected",
    [
        pytest.param("<tag></tag>", "element", None, id="No Elements"),
        pytest.param(
            "<tag><element></element></tag>", "element", None, id="Empty Element"
        ),
        pytest.param(
            "<tag><element>invalid_datetime</element></tag>",
            "element",
            None,
            id="Invalid Datetime Element",
        ),
        pytest.param(
            "<tag><element>2023-06-17T10:30:00</element></tag>",
            "element",
            datetime(2023, 6, 17, 10, 30),
            id="Valid Datetime Element",
        ),
    ],
)
def test_get_element_datetime(
    xml_string: str, field_name: str, expected: datetime | None
):
    """
    Test getting and converting element text to a datetime
    """
    root = etree.fromstring(xml_string)
    assert get_element_datetime(root, field_name) == expected


@pytest.mark.parametrize(
    "xml_string, field_name, expected",
    [
        pytest.param("<tag></tag>", "element", None, id="No Elements"),
        pytest.param(
            "<tag><element></element></tag>", "element", None, id="Empty Element"
        ),
        pytest.param(
            "<tag><element>invalid_date</element></tag>",
            "element",
            None,
            id="Invalid Date Element",
        ),
        pytest.param(
            "<tag><element>2023-06-17</element></tag>",
            "element",
            date(2023, 6, 17),
            id="Valid Date Element",
        ),
    ],
)
def test_get_element_date(xml_string: str, field_name: str, expected: date | None):
    """
    Test getting and converting element text to a date
    """
    root = etree.fromstring(xml_string)
    assert get_element_date(root, field_name) == expected


@pytest.mark.parametrize(
    "xml_string, field_name, expected",
    [
        pytest.param("<tag></tag>", "element", None, id="No Elements"),
        pytest.param(
            "<tag><element></element></tag>", "element", None, id="Empty Element"
        ),
        pytest.param(
            "<tag><element>invalid_bool</element></tag>",
            "element",
            None,
            id="Invalid Bool Element",
        ),
        pytest.param(
            "<tag><element>true</element></tag>",
            "element",
            True,
            id="Valid Bool Element (True)",
        ),
        pytest.param(
            "<tag><element>false</element></tag>",
            "element",
            False,
            id="Valid Bool Element (False)",
        ),
    ],
)
def test_get_element_bool(xml_string: str, field_name: str, expected: bool | None):
    """
    Test getting and converting element text to a bool
    """
    root = etree.fromstring(xml_string)
    assert get_element_bool(root, field_name) == expected


@pytest.mark.parametrize(
    "xml_string, field_name, default, expected",
    [
        pytest.param("<tag></tag>", "element", False, False, id="No Elements"),
        pytest.param(
            "<tag><element></element></tag>", "element", True, True, id="Empty Element"
        ),
        pytest.param(
            "<tag><element>invalid_bool</element></tag>",
            "element",
            False,
            False,
            id="Invalid Bool Element",
        ),
        pytest.param(
            "<tag><element>true</element></tag>",
            "element",
            False,
            True,
            id="Valid Bool Element (True)",
        ),
        pytest.param(
            "<tag><element>false</element></tag>",
            "element",
            True,
            False,
            id="Valid Bool Element (False)",
        ),
    ],
)
def test_get_elem_bool_default(
    xml_string: str, field_name: str, default: bool, expected: bool
):
    """
    Test getting and converting element text to a bool with a default value
    """
    root = etree.fromstring(xml_string)
    assert get_elem_bool_default(root, field_name, default) == expected
