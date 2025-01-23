from lxml import etree
from pti.app.validators.operator import validate_licence_number

from tests.timetables_etl.pti.validators.test_functions import DATA_DIR

NAMESPACE = {"x": "http://www.transxchange.org.uk/"}


def test_validate_licence_number_coach_data():
    """
    This test case validates LicenceNumber is not a mandatory element for Operators with PrimaryMode as Coach
    """

    string_xml = DATA_DIR / "coaches" / "coach_operator.xml"
    with string_xml.open("r") as txc_xml:
        doc = etree.parse(txc_xml)
        elements = doc.xpath("//x:Operator", namespaces=NAMESPACE)
        actual = validate_licence_number("", elements)
        assert actual == True


def test_validate_licence_number_non_coach_data_success():
    """
    This test case validates LicenceNumber is a mandatory element for Non Coach Operators
    """
    string_xml = DATA_DIR / "coaches" / "non_coach_data_operator.xml"
    with string_xml.open("r") as txc_xml:
        doc = etree.parse(txc_xml)
        elements = doc.xpath("//x:Operator", namespaces=NAMESPACE)
        actual = validate_licence_number("", elements)
        assert actual == True


def test_validate_licence_number_non_coach_data_failed():
    """
    This test case validates LicenceNumber is a mandatory element for Non Coach Operators
    """
    string_xml = (
        DATA_DIR / "coaches" / "non_coach_data_operator_without_licence_number.xml"
    )
    with string_xml.open("r") as txc_xml:
        doc = etree.parse(txc_xml)
        elements = doc.xpath("//x:Operator", namespaces=NAMESPACE)
        actual = validate_licence_number("", elements)
        assert actual == False
