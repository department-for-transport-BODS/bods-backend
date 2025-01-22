"""
Test Services Observation 20
Mandatory element incorrect in 'OperatingPeriod'. 
"""

from datetime import timedelta
from pathlib import Path

import pytest
from dateutil import parser

from tests.timetables_etl.pti.validators.conftest import TXCFile, create_validator

DATA_DIR = Path(__file__).parent / "data/services"
OBSERVATION_ID = 20


@pytest.mark.parametrize(
    "start_date, end_date_in_days, expected",
    [
        pytest.param("2005-01-01", None, True, id="Valid No End Date"),
        pytest.param("2005-01-01", 0, True, id="Valid Same Day End"),
        pytest.param("2005-01-01", 1, True, id="Valid Next Day End"),
        pytest.param("2005-01-01", 365, True, id="Valid One Year End"),
        pytest.param("2005-01-01", 366, True, id="Valid Leap Year End"),
        pytest.param("2005-01-01", 4026, True, id="Valid Maximum Period (11 Years)"),
        pytest.param("2005-01-01", 4027, False, id="Invalid Exceeds Maximum Period"),
        pytest.param("2005-01-01", 8000, False, id="Invalid Far Future End"),
        pytest.param("2005-01-01", -1, False, id="Invalid Past End Date"),
    ],
)
def test_operating_period_end_date(
    start_date: str, end_date_in_days: int | None, expected: bool
):
    """
    Test validation of service operating period dates
    Validates that operating periods have valid start and end dates within allowed ranges
    Maximum allowed period is 11 years (4026 days)
    """
    service_template = """
   <Service>
       <ServiceCode>025</ServiceCode>
       <Lines>
           <Line id="2">
               <LineName>215</LineName>
           </Line>
           <Line id="90">
               <LineName>215A</LineName>
           </Line>
       </Lines>
       <OperatingPeriod>
           {0}
           {1}
       </OperatingPeriod>
   </Service>
   """

    if end_date_in_days is not None:
        end_date = parser.parse(start_date) + timedelta(days=end_date_in_days)
        end_date = f"<EndDate>{end_date:%Y-%m-%d}</EndDate>"
    else:
        end_date = ""

    start_date = f"<StartDate>{start_date}</StartDate>"
    xml = service_template.format(start_date, end_date)

    pti, _ = create_validator("dummy.xml", DATA_DIR, OBSERVATION_ID)
    is_valid = pti.is_valid(TXCFile(xml))
    assert is_valid == expected
