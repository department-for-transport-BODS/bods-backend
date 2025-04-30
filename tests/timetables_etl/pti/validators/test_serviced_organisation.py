"""
Tests for Service Organisation PTI
"""

from pathlib import Path

from lxml import etree
from pti.app.constants import NAMESPACE
from pti.app.validators.serviced_organisation import (
    has_servicedorganisation_working_days,
)

DATA_DIR = Path(__file__).parent / "data/servicedorganisations"


def test_has_servicedorganisation_working_days_not_present() -> None:
    """
    This test case validates working days tag is present for ServicedOrganisation
    """

    string_xml = DATA_DIR / "servicedorganisation_working_days_not_present.xml"
    with string_xml.open("r") as txc_xml:
        doc = etree.parse(txc_xml)
        elements = doc.xpath(
            "//x:ServicedOrganisations/x:ServicedOrganisation", namespaces=NAMESPACE
        )
        actual = has_servicedorganisation_working_days(None, elements)
        assert actual is False


def test_has_servicedorganisation_working_days_present():
    """
    This test case validates working days tag is present for ServicedOrganisation
    """
    string_xml = DATA_DIR / "servicedorganisation_working_days_present.xml"
    with string_xml.open("r") as txc_xml:
        doc = etree.parse(txc_xml)
        elements = doc.xpath(
            "//x:ServicedOrganisations/x:ServicedOrganisation", namespaces=NAMESPACE
        )
        actual = has_servicedorganisation_working_days(None, elements)
        assert actual is True
