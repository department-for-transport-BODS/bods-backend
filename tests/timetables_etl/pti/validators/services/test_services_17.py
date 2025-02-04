"""
Test Services Observation 17
Mandatory elements incorrect in 'ServicesGroup'.
"""

import pytest

from tests.timetables_etl.pti.validators.conftest import TXCFile, create_validator

from .conftest import DATA_DIR

OBSERVATION_ID = 17


@pytest.mark.parametrize(
    "no_of_services, expected",
    [
        pytest.param(2, False, id="Invalid Multiple Services"),
        pytest.param(0, False, id="Invalid No Services"),
    ],
)
def test_start_date_provisional_invalid(no_of_services: int, expected: bool):
    """Test validation of service count and start dates"""
    service_template = """
   <Service>
       <ServiceCode>{}</ServiceCode>
       <Lines>
           <Line id="L1">
               <LineName>1A</LineName>
           </Line>
           <Line id="L2">
               <LineName>1B</LineName>
           </Line>
       </Lines>
       <OperatingPeriod>
           <StartDate>2004-01-01</StartDate>
           <EndDate>2005-06-13</EndDate>
       </OperatingPeriod>
   </Service>
   """
    services = "\n".join(
        [
            service_template.format(service_code)
            for service_code in range(no_of_services)
        ]
    )
    xml = f"<Services>{services}</Services>"

    pti, _ = create_validator("dummy.xml", DATA_DIR, OBSERVATION_ID)
    is_valid = pti.is_valid(TXCFile(xml))
    assert is_valid == expected


@pytest.mark.parametrize(
    "_no_of_services, expected",
    [
        pytest.param(1, True, id="Valid Single Service With Standard Service"),
    ],
)
def test_start_date_provisional_valid(_no_of_services: int, expected: bool):
    """Test validation of a single service with operating period and standard service"""
    service_template = """
   <Service>
       <ServiceCode>{}</ServiceCode>
       <Lines>
           <Line id="L1">
               <LineName>1A</LineName>
           </Line>
           <Line id="L2">
               <LineName>1B</LineName>
           </Line>
       </Lines>
       <OperatingPeriod>
           <StartDate>2004-01-01</StartDate>
           <EndDate>2005-06-13</EndDate>
       </OperatingPeriod>
       <StandardService>
           <Origin>Putteridge High School</Origin>
       </StandardService>
   </Service>
   """
    service_code = "PB0002032:467"
    services = "\n".join([service_template.format(service_code)])
    xml = f"<Services>{services}</Services>"

    pti, _ = create_validator("dummy.xml", DATA_DIR, OBSERVATION_ID)
    is_valid = pti.is_valid(TXCFile(xml))
    assert is_valid == expected
