"""
PTI Holiday Tests
"""

from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from common_layer.pti.models import Schema
from pti.app.constants import PTI_SCHEMA_PATH
from pti.app.validators.pti import PTIValidator

from tests.timetables_etl.pti.validators.conftest import JSONFile

DATA_DIR = Path(__file__).parent / "data" / "holidays"

OBSERVATION_ID = 43


def create_validator(filename: str) -> tuple[PTIValidator, Path]:
    """Helper function to create PTIValidator instance and file path"""
    schema = Schema.from_path(PTI_SCHEMA_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema.observations = observations
    json_file = JSONFile(schema.model_dump_json())
    pti = PTIValidator(json_file, MagicMock(), MagicMock())
    return pti, DATA_DIR / filename


@pytest.mark.parametrize(
    "filename, is_scottish",
    [
        pytest.param("scottish_holidays.xml", True, id="Valid Scottish Holidays"),
        pytest.param("english_holidays.xml", False, id="Valid English Holidays"),
    ],
)
def test_bank_holidays_valid(filename: str, is_scottish: bool):
    """
    Test validation of valid bank holiday data in TXC files
    Covers both Scottish and English holiday patterns
    """
    with patch(
        "pti.app.validators.holidays.is_service_in_scotland", return_value=is_scottish
    ):
        pti, txc_path = create_validator(filename)

        with txc_path.open("rb") as txc:
            is_valid = pti.is_valid(BytesIO(txc.read()))

        assert is_valid is True


@pytest.mark.parametrize(
    "filename, is_scottish",
    [
        pytest.param(
            "scottish_holidays_error.xml", True, id="Invalid Scottish Holidays"
        ),
        pytest.param(
            "english_holidays_error.xml", False, id="Invalid English Holidays"
        ),
    ],
)
def test_bank_holidays_invalid(filename: str, is_scottish: bool):
    """
    Test validation of invalid bank holiday data in TXC files
    Covers both Scottish and English holiday patterns with errors
    """
    with patch(
        "pti.app.validators.holidays.is_service_in_scotland", return_value=is_scottish
    ):
        pti, txc_path = create_validator(filename)

        with txc_path.open("rb") as txc:
            is_valid = pti.is_valid(BytesIO(txc.read()))

        assert is_valid is False
