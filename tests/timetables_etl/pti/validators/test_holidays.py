"""
PTI Holiday Tests
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from .conftest import run_validation

DATA_DIR = Path(__file__).parent / "data" / "holidays"

OBSERVATION_ID = 43


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
        is_valid = run_validation(filename, DATA_DIR, OBSERVATION_ID)
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
        is_valid = run_validation(filename, DATA_DIR, OBSERVATION_ID)

        assert is_valid is False
