"""
Test Valid XMLs in the dangerous_xml_check
"""

from xml.etree.ElementTree import ElementTree

import pytest
from file_validation.app.xml_checks import dangerous_xml_check


@pytest.mark.parametrize(
    "xml_content",
    [
        pytest.param(
            b"""<?xml version="1.0" encoding="UTF-8"?>
            <root><child>Simple valid XML</child></root>""",
            id="Valid XML",
        ),
        pytest.param(
            b"""<?xml version="1.0" encoding="UTF-8"?>
            <root>
                <child id="1">Nested content</child>
                <child id="2">More content</child>
            </root>""",
            id="Nested XML",
        ),
        pytest.param(
            b"""<?xml version="1.0" encoding="UTF-8"?>
            <root xmlns:test="http://test.com">
                <test:child>XML with namespace</test:child>
            </root>""",
            id="XML with Namespace",
        ),
    ],
)
def test_valid_xml_parsing(create_xml_file, xml_content: bytes) -> None:
    """
    Test parsing of valid XML documents.

    Args:
        create_xml_file: Fixture to create XML file objects
        xml_content: Valid XML content to test
        test_name: Name of the test case
    """
    xml_file = create_xml_file(xml_content)
    result = dangerous_xml_check(xml_file, "test.xml")
    assert isinstance(result, ElementTree)
