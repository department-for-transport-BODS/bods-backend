from multiprocessing import Value
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from common_layer.pti.models import Schema
from pti.constants import PTI_SCHEMA_PATH
from pti.validators.pti import PTIValidator

from tests.timetables_etl.pti.validators.conftest import JSONFile
from tests.timetables_etl.pti.validators.factories import SchemaFactory

DATA_DIR = Path(__file__).parent / "data"


def test_is_valid_missing_metadata():
    filename = "missing_filename_metadata.xml"
    OBSERVATION_ID = 2
    schema = Schema.from_path(PTI_SCHEMA_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.model_dump_json())
    pti = PTIValidator(json_file, MagicMock(), MagicMock())
    txc_path = DATA_DIR / filename
    with txc_path.open("r") as txc:
        with pytest.raises(
            ValueError, match="Missing metadata in XML file root element"
        ):
            pti.is_valid(txc)
