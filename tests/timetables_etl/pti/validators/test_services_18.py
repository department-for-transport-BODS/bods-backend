"""
Test Services Observation 18
Mandatory elements incorrect in the 'ServiceCode' field.
"""

from pathlib import Path

import pytest

from tests.timetables_etl.pti.validators.conftest import TXCFile, create_validator

DATA_DIR = Path(__file__).parent / "data/services"
OBSERVATION_ID = 18


@pytest.mark.parametrize(
    "service_code, expected",
    [
        pytest.param("S1", False, id="Invalid Simple Service Code"),
        pytest.param("PF0000459:134", True, id="Valid NOC With Numeric Line"),
        pytest.param("PF0000459:", False, id="Invalid Missing Line Number"),
        pytest.param("PF0000459:ABC", True, id="Valid NOC With Alphanumeric Line"),
        pytest.param("PD1073423:4", True, id="Valid Short NOC Format"),
        pytest.param("UZ000WNCT:GTT32", True, id="Valid Complex Line Number"),
        pytest.param("PD0001111:6:7", False, id="Invalid Multiple Colons"),
    ],
)
def test_service_code_format(service_code: str, expected: bool):
    """
    Test validation of service code formats
    Validates that service codes follow the format NOC:Line
    where NOC is a valid National Operator Code
    """
    services_template = """
   <Services>
       <Service>
           <ServiceCode>{0}</ServiceCode>
       </Service>
   </Services>
   """
    xml = services_template.format(service_code)

    pti, _ = create_validator("dummy.xml", DATA_DIR, OBSERVATION_ID)
    is_valid = pti.is_valid(TXCFile(xml))
    assert is_valid == expected
