"""
Netex Fixtures / Utils
"""

from common_layer.xml.netex.parser import NETEX_NS
from lxml import etree
from lxml.etree import _Element  # type: ignore


def parse_xml_str_as_netex(xml_str: str) -> _Element:
    """
    Parse an XML string and add NeTEx namespace.
    Makes test XML easier to read by handling namespaces at parse time.
    """
    # Strip whitespace and newlines
    xml_str = "".join(line.strip() for line in xml_str.splitlines())
    print(xml_str)
    # Add namespace to element
    first_space = xml_str.find(" ")
    first_close = xml_str.find(">")
    insert_pos = (
        first_space if first_space != -1 and first_space < first_close else first_close
    )
    xml_with_ns = f'{xml_str[:insert_pos]} xmlns="{NETEX_NS}"{xml_str[insert_pos:]}'

    return etree.fromstring(xml_with_ns)


def parse_xml_str_as_netex_wrapped(xml_str: str) -> _Element:
    """
    Parse an XML string as a child of a parent element with NeTEx namespace.
    Useful when you need to search within the element.
    """
    # Strip whitespace and newlines
    xml_str = "".join(line.strip() for line in xml_str.splitlines())

    # Wrap in parent element with namespace
    wrapped = f'<Parent xmlns="{NETEX_NS}">{xml_str}</Parent>'

    return etree.fromstring(wrapped)
