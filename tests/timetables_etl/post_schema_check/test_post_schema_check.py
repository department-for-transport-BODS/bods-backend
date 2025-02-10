"""
Tests for Post Schema Checks
"""

from datetime import datetime

import pytest
from common_layer.xml.txc.models.txc_data import TXCData
from common_layer.xml.txc.models.txc_metadata import TXCMetadata
from post_schema_check.app.models import ValidationResult
from post_schema_check.app.post_schema_check import process_txc_data_check
from post_schema_check.app.validators import check_filename_for_filepath_pii


@pytest.mark.parametrize(
    "filename, expected_valid, expected_error",
    [
        pytest.param(
            "C:\\Users\\Jon\\Documents\\transit.xml",
            False,
            "PII_ERROR",
            id="Windows filepath with multiple backslashes",
        ),
        pytest.param(
            "\\\\networkshare\\folder\\file.xml",
            False,
            "PII_ERROR",
            id="Network path with backslashes",
        ),
        pytest.param(
            "/home/john/documents/transit.xml",
            False,
            "PII_ERROR",
            id="Unix filepath with forward slashes",
        ),
        pytest.param(
            "/Users/Jon/Documents/transit.xml",
            False,
            "PII_ERROR",
            id="OSX filepath with forward slashes",
        ),
        pytest.param(
            "simple_filename.xml",
            True,
            None,
            id="Simple filename without path",
        ),
        pytest.param(
            None,
            True,
            None,
            id="None input",
        ),
        pytest.param(
            "file\\",
            False,
            "PII_ERROR",
            id="Single backslash",
        ),
        pytest.param(
            "file/",
            False,
            "PII_ERROR",
            id="Single forward slash",
        ),
        pytest.param(
            "~/.local/share/file.xml",
            False,
            "PII_ERROR",
            id="Unix home directory shorthand",
        ),
    ],
)
def test_validate_filepath_pii(
    filename: str | None, expected_valid: bool, expected_error: str | None
):
    """
    Test checking filenames for potential PII in filepath information
    Covers both Windows and Unix-style paths
    """
    txc_data = TXCData(
        Metadata=(
            None
            if filename is None
            else TXCMetadata(
                SchemaVersion="2.4",
                ModificationDateTime=datetime.now(),
                Modification="new",
                RevisionNumber=1,
                CreationDateTime=datetime.now(),
                FileName=filename,
            )
        )
    )

    result = check_filename_for_filepath_pii(txc_data)
    assert isinstance(result, ValidationResult)
    assert result.is_valid == expected_valid
    assert result.error_code == expected_error


@pytest.mark.parametrize(
    "filename, expected_violations",
    [
        pytest.param(
            "C:\\Users\\Jon\\file.xml",
            [
                ValidationResult(
                    is_valid=False,
                    error_code="PII_ERROR",
                    message="Filename contains potential filepath PII",
                )
            ],
            id="File with PII violation",
        ),
        pytest.param(
            "valid_file.xml",
            [],
            id="Valid filename without violations",
        ),
        pytest.param(
            None,
            [],
            id="None metadata",
        ),
    ],
)
def test_process_txc_data_check(filename: str | None, expected_violations: list[str]):
    """
    Test the overall validation process
    """
    txc_data = TXCData(
        Metadata=(
            None
            if filename is None
            else TXCMetadata(
                SchemaVersion="2.4",
                ModificationDateTime=datetime.now(),
                Modification="new",
                RevisionNumber=1,
                CreationDateTime=datetime.now(),
                FileName=filename,
            )
        )
    )

    assert process_txc_data_check(txc_data) == expected_violations
