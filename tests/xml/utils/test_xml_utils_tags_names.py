"""
Tag Name Extraction
"""

import pytest
from common_layer.xml.utils import get_tag_name, get_tag_str
from lxml.etree import Element, QName, _Element  # type: ignore


@pytest.mark.parametrize(
    "input_xml,expected",
    [
        pytest.param(
            Element("{http://www.siri.org.uk/siri}StopPoint"),
            "{http://www.siri.org.uk/siri}StopPoint",
            id="Namespaced tag",
        ),
        pytest.param(
            Element("SimpleTag"),
            "SimpleTag",
            id="Simple tag without namespace",
        ),
        pytest.param(
            Element("{http://example.com}Tag-with-hyphen"),
            "{http://example.com}Tag-with-hyphen",
            id="Namespaced tag with hyphen",
        ),
        pytest.param(
            Element("{urn:x-custom}CustomElement"),
            "{urn:x-custom}CustomElement",
            id="Tag with URN namespace",
        ),
    ],
)
def test_get_tag_str(input_xml: _Element, expected: str) -> None:
    """Test get_tag_str function with various tag formats."""
    result = get_tag_str(input_xml)
    assert result == expected


@pytest.mark.parametrize(
    "input_xml,expected",
    [
        pytest.param(
            Element("{http://www.siri.org.uk/siri}StopPoint"),
            "StopPoint",
            id="Extract name from namespaced tag",
        ),
        pytest.param(
            Element("SimpleTag"),
            "SimpleTag",
            id="Return simple tag unchanged",
        ),
        pytest.param(
            Element("{http://example.com}Tag-with-hyphen"),
            "Tag-with-hyphen",
            id="Handle hyphenated tag name",
        ),
        pytest.param(
            Element("{urn:x-custom}CustomElement"),
            "CustomElement",
            id="Handle URN namespace",
        ),
    ],
)
def test_get_tag_name(input_xml: _Element, expected: str) -> None:
    """Test get_tag_name function with various tag formats."""
    result = get_tag_name(input_xml)
    assert result == expected


def test_get_tag_str_with_qname() -> None:
    """Test get_tag_str function with QName object."""
    qname = QName("http://www.siri.org.uk/siri", "StopPoint")
    elem = Element(qname)
    result = get_tag_str(elem)
    assert result == "{http://www.siri.org.uk/siri}StopPoint"


def test_get_tag_name_with_qname() -> None:
    """Test get_tag_name function with QName object."""
    qname = QName("http://www.siri.org.uk/siri", "StopPoint")
    elem = Element(qname)
    result = get_tag_name(elem)
    assert result == "StopPoint"
