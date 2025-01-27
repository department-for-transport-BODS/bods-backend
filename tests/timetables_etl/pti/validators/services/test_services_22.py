"""
Test Services Observation 21
Mandatory elements incorrect in 'StandardService' field
"""

import pytest

from tests.timetables_etl.pti.validators.conftest import TXCFile, create_validator

from .conftest import DATA_DIR

OBSERVATION_ID = 22


@pytest.mark.parametrize(
    "service_type, expected",
    [
        pytest.param("FlexibleService", True, id="Valid Flexible Service"),
        pytest.param("StandardService", True, id="Valid Standard Service"),
        pytest.param("", False, id="Invalid Missing Service Type"),
    ],
)
def test_flexible_service(service_type: str, expected: bool):
    """
    Test validation of service types
    Validates that services are either Flexible or Standard type
    """
    service_xml = ""
    if service_type:
        if service_type == "FlexibleService":
            service_xml = (
                "<ServiceClassification><Flexible/></ServiceClassification>"
                f"<{service_type}></{service_type}>"
            )
        else:
            service_xml = f"<{service_type}></{service_type}>"

    service_template = """
   <Service>
       <ServiceCode>FIN50</ServiceCode>
       <Lines>
           <Line id="l_1">
               <LineName>A1</LineName>
           </Line>
       </Lines>
       {0}
   </Service>
   """

    service = service_template.format(service_xml)
    xml = f"<Services>{service}</Services>"

    pti, _ = create_validator("dummy.xml", DATA_DIR, OBSERVATION_ID)
    is_valid = pti.is_valid(TXCFile(xml))
    assert is_valid == expected
