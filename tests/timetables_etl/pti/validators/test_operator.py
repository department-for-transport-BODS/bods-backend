"""
Test Operator Tags
"""

from pathlib import Path

import pytest
from lxml import etree
from pti.app.constants import NAMESPACE
from pti.app.validators.operator import validate_licence_number

DATA_DIR = Path(__file__).parent / "data/coaches"


@pytest.mark.parametrize(
    "filename,expected",
    [
        pytest.param(
            "coach_operator.xml", True, id="Coach operator without license number"
        ),
        pytest.param(
            "non_coach_data_operator.xml",
            True,
            id="Non-coach operator with license number",
        ),
        pytest.param(
            "non_coach_data_operator_without_licence_number.xml",
            False,
            id="Non-coach operator without license number",
        ),
    ],
)
def test_validate_licence_number(filename: str, expected: bool) -> None:
    """Tests license number validation for coach and non-coach operators"""
    filepath = DATA_DIR / filename
    with filepath.open("r") as txc_xml:
        doc = etree.parse(txc_xml)
        elements = doc.xpath("//x:Operator", namespaces=NAMESPACE)
        assert validate_licence_number(None, elements) == expected
