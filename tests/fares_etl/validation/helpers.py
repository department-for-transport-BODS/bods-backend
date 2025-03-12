from lxml import etree

from fares_etl.validation.app.constants import NAMESPACE


def get_lxml_element(xpath: str, string_xml: str):
    doc = etree.fromstring(string_xml)
    elements = doc.xpath(xpath, namespaces=NAMESPACE)
    return elements
