"""
Tests for Service Organisation PTI
"""

from lxml import etree
from pti.app.validators.serviced_organisation import (
    has_servicedorganisation_working_days,
)

from tests.timetables_etl.pti.validators.test_functions import DATA_DIR


def test_has_servicedorganisation_working_days_not_present():
    """
    This test case validates working days tag is present for ServicedOrganisation
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    string_xml = (
        DATA_DIR
        / "servicedorganisations"
        / "servicedorganisation_working_days_not_present.xml"
    )
    with string_xml.open("r") as txc_xml:
        doc = etree.parse(txc_xml)
        elements = doc.xpath(
            "//x:ServicedOrganisations/x:ServicedOrganisation", namespaces=NAMESPACE
        )
        actual = has_servicedorganisation_working_days("", elements)
        assert actual == False


def test_has_servicedorganisation_working_days_present():
    """
    This test case validates working days tag is present for ServicedOrganisation
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    string_xml = (
        DATA_DIR
        / "servicedorganisations"
        / "servicedorganisation_working_days_present.xml"
    )
    with string_xml.open("r") as txc_xml:
        doc = etree.parse(txc_xml)
        elements = doc.xpath(
            "//x:ServicedOrganisations/x:ServicedOrganisation", namespaces=NAMESPACE
        )
        actual = has_servicedorganisation_working_days("", elements)
        assert actual == True
