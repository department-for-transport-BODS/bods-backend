"""
Test Validations
"""

import pytest
from file_attributes_etl.app.process_txc import (
    validate_filename,
    validate_schema_version,
)


@pytest.mark.parametrize(
    "input_version,expected_version",
    [
        pytest.param(
            "2.4",
            "2.4",
            id="Valid Schema Version 2.4",
        ),
    ],
)
def test_validate_schema_version_valid(
    input_version: str, expected_version: str
) -> None:
    """Test validate_schema_version accepts valid schema versions."""
    result = validate_schema_version(input_version)
    assert result == expected_version


@pytest.mark.parametrize(
    "input_version",
    [
        pytest.param(
            "2.1",
            id="Invalid Schema Version",
        ),
        pytest.param(
            None,
            id="None Schema Version",
        ),
        pytest.param(
            "3.0",
            id="Future Schema Version",
        ),
    ],
)
def test_validate_schema_version_invalid(input_version: str | None) -> None:
    """Test validate_schema_version raises error for invalid versions."""
    with pytest.raises(ValueError, match="SCHEMA_VERSION_NOT_SUPPORTED"):
        validate_schema_version(input_version)


@pytest.mark.parametrize(
    "input_filename,expected_filename",
    [
        pytest.param(
            "test_file.xml",
            "test_file.xml",
            id="Already Valid XML Extension",
        ),
        pytest.param(
            "test_file.json",
            "test_file.json.xml",
            id="JSON File Needs XML Extension",
        ),
        pytest.param(
            "test_file",
            "test_file.xml",
            id="No Extension Needs XML",
        ),
        pytest.param(
            "complex.name.file",
            "complex.name.file.xml",
            id="Multiple Dots In Filename",
        ),
    ],
)
def test_validate_filename(
    input_filename: str,
    expected_filename: str,
) -> None:
    """Test validate_filename function returns expected filenames."""
    result = validate_filename(input_filename)
    assert result == expected_filename
