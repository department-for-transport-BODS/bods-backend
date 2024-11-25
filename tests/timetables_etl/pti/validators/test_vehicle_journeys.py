from pathlib import Path

import pytest
from pti.constants import PTI_SCHEMA_PATH
from pti.models import Schema
from pti.validators.pti import PTIValidator

from tests.timetables_etl.pti.validators.conftest import JSONFile
from tests.timetables_etl.pti.validators.factories import SchemaFactory

DATA_DIR = Path(__file__).parent / "data/vehicle_journeys"


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("destinationdisplayjourneypattern.xml", True),
        ("dynamicdisplaytiminglinks.xml", True),
        ("dynamicdisplaytiminglinksfail.xml", False),
    ],
)
def test_destination_display(filename, expected):
    OBSERVATION_ID = 47
    schema = Schema.from_path(PTI_SCHEMA_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    txc_path = DATA_DIR / filename

    with txc_path.open("r") as txc:
        is_valid = pti.is_valid(txc)
    assert is_valid == expected
