import pytest
from pathlib import Path
from lxml import etree
from pti.constants import PTI_PATH
from pti.models import Schema
from pti.validators.pti import PTIValidator
from tests.timetables_etl.pti.validators.conftest import JSONFile
from tests.timetables_etl.pti.validators.factories import SchemaFactory

# Define the directory for test data
DATA_DIR = Path(__file__).parent / "data"


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("bodp3615stoppoints.xml", True),
        ("bodp3615stoppointsfail2month.xml", False),
        ("bodp3615stoppointsfailnodate.xml", False),
        ("stoppointsinheritfromservice2months.xml", True),
        ("stoppointsinheritfromservice2monthsplus.xml", False),
        ("stoppointsinheritstartdatefromservice.xml", True),
        ("stoppointsinheritenddatefromservice.xml", True),
    ]
)
def test_validate(filename, expected):
    OBSERVATION_ID = 28
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]

    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc_path = DATA_DIR / filename
    with txc_path.open("r") as txc:
        is_valid = pti.is_valid(txc)
    assert is_valid == expected