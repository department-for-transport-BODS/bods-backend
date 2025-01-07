from pathlib import Path
from unittest.mock import MagicMock, patch

from common_layer.pti.constants import PTI_SCHEMA_PATH
from common_layer.pti.models import Schema
from pti.validators.pti import PTIValidator

from tests.timetables_etl.pti.validators.conftest import JSONFile
from tests.timetables_etl.pti.validators.factories import SchemaFactory

DATA_DIR = Path(__file__).parent / "data" / "holidays"


@patch("pti.validators.holidays.is_service_in_scotland", return_value=True)
def test_bank_holidays_scottish_holidays(m_is_service_in_scotland):
    filename = "scottish_holidays.xml"
    OBSERVATION_ID = 43
    schema = Schema.from_path(PTI_SCHEMA_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.model_dump_json())
    pti = PTIValidator(json_file, MagicMock(), MagicMock())
    txc_path = DATA_DIR / filename

    with txc_path.open("r") as txc:
        is_valid = pti.is_valid(txc)
    assert is_valid


@patch("pti.validators.holidays.is_service_in_scotland", return_value=True)
def test_bank_holidays_scottish_holidays_error(m_is_service_in_scotland):
    filename = "scottish_holidays_error.xml"
    OBSERVATION_ID = 43
    schema = Schema.from_path(PTI_SCHEMA_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.model_dump_json())
    pti = PTIValidator(json_file, MagicMock(), MagicMock())
    txc_path = DATA_DIR / filename

    with txc_path.open("r") as txc:
        is_valid = pti.is_valid(txc)
    assert is_valid is False


@patch("pti.validators.holidays.is_service_in_scotland", return_value=False)
def test_bank_holidays_english_holidays(m_is_service_in_scotland):
    filename = "english_holidays.xml"
    OBSERVATION_ID = 43
    schema = Schema.from_path(PTI_SCHEMA_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.model_dump_json())
    pti = PTIValidator(json_file, MagicMock(), MagicMock())
    txc_path = DATA_DIR / filename

    with txc_path.open("r") as txc:
        is_valid = pti.is_valid(txc)
    assert is_valid


@patch("pti.validators.holidays.is_service_in_scotland", return_value=False)
def test_bank_holidays_english_holidays_error(m_is_service_in_scotland):
    filename = "english_holidays_error.xml"
    OBSERVATION_ID = 43
    schema = Schema.from_path(PTI_SCHEMA_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.model_dump_json())
    pti = PTIValidator(json_file, MagicMock(), MagicMock())
    txc_path = DATA_DIR / filename

    with txc_path.open("r") as txc:
        is_valid = pti.is_valid(txc)
    assert is_valid is False
