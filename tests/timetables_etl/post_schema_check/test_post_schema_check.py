"""
Tests for Post Schema Checks
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from common_layer.xml.txc.models import TXCData
from common_layer.xml.txc.models.txc_metadata import TXCMetadata
from post_schema_check.app.models import ValidationResult
from post_schema_check.app.post_schema_check import process_txc_data_check
from post_schema_check.app.validators import (
    check_filename_for_filepath_pii,
    check_service_code_exists,
)

from tests.factories.database.organisation import (
    OrganisationDatasetFactory,
    OrganisationDatasetRevisionFactory,
    OrganisationTXCFileAttributesFactory,
)
from tests.timetables_etl.factories.txc.factory_txc_data import TXCDataFactory
from tests.timetables_etl.factories.txc.factory_txc_service import TXCServiceFactory


@pytest.fixture(name="txc_data")
def mock_txc_data():
    """Mock TXCData Object with Services"""
    return TXCDataFactory(
        Services=[
            TXCServiceFactory(ServiceCode="SC123"),
            TXCServiceFactory(ServiceCode="SC456"),
        ]
    )


@pytest.mark.parametrize(
    "filename, expected_valid, expected_error",
    [
        pytest.param(
            "C:\\Users\\Jon\\Documents\\transit.xml",
            False,
            "PII ERROR",
            id="Windows filepath with multiple backslashes",
        ),
        pytest.param(
            "\\\\networkshare\\folder\\file.xml",
            False,
            "PII ERROR",
            id="Network path with backslashes",
        ),
        pytest.param(
            "/home/john/documents/transit.xml",
            False,
            "PII ERROR",
            id="Unix filepath with forward slashes",
        ),
        pytest.param(
            "/Users/Jon/Documents/transit.xml",
            False,
            "PII ERROR",
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
            "PII ERROR",
            id="Single backslash",
        ),
        pytest.param(
            "file/",
            False,
            "PII ERROR",
            id="Single forward slash",
        ),
        pytest.param(
            "~/.local/share/file.xml",
            False,
            "PII ERROR",
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

    result = check_filename_for_filepath_pii(txc_data, Mock())
    assert isinstance(result, list)
    assert result[0].is_valid == expected_valid
    assert result[0].error_code == expected_error


@pytest.mark.parametrize(
    "filename, expected_violations",
    [
        pytest.param(
            "C:\\Users\\Jon\\file.xml",
            [
                ValidationResult(
                    is_valid=False,
                    error_code="PII ERROR",
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

    assert process_txc_data_check(txc_data, Mock()) == expected_violations


def test_no_service_codes_provided():
    """
    Test Case 1: No Service Codes Provided
    """
    txc_data = TXCDataFactory(Services=[])  # Empty Services List
    result = check_service_code_exists(txc_data, Mock())
    assert result == [ValidationResult(is_valid=True)]


def test_service_codes_not_found(mock_txc_file_attributes_repo, txc_data):
    """
    Service Codes Not Found in TXC Attributes
    """
    mock_txc_file_attributes_repo.get_by_service_code.return_value = []

    with patch(
        "post_schema_check.app.validators.check_service_code_exists.OrganisationTXCFileAttributesRepo",
        return_value=mock_txc_file_attributes_repo,
    ):
        result = check_service_code_exists(txc_data, Mock())

        assert len(result) == 1
        assert result[0].is_valid is True
        assert result[0].error_code is None
        assert result[0].message is None

        mock_txc_file_attributes_repo.get_by_service_code.assert_called_once_with(
            ["SC123", "SC456"]
        )


def test_service_codes_found_no_active_datasets(
    mock_txc_file_attributes_repo,
    mock_revision_repo,
    txc_data,
):
    """
    Service Codes Found but No Active Dataset Revisions
    """
    mock_txc_file_attributes_repo.get_by_service_code.return_value = [
        MagicMock(id=1, service_code="SC123", revision_id=1),
        MagicMock(id=2, service_code="SC456", revision_id=2),
    ]
    mock_revision_repo.get_live_revisions.return_value = []  # No active revisions

    with (
        patch(
            "post_schema_check.app.validators.check_service_code_exists.OrganisationTXCFileAttributesRepo",
            return_value=mock_txc_file_attributes_repo,
        ),
        patch(
            "post_schema_check.app.validators.check_service_code_exists.OrganisationDatasetRevisionRepo",
            return_value=mock_revision_repo,
        ),
    ):
        result = check_service_code_exists(txc_data, Mock())

        assert result == [ValidationResult(is_valid=True)]
        mock_txc_file_attributes_repo.get_by_service_code.assert_called_once_with(
            ["SC123", "SC456"]
        )
        mock_revision_repo.get_live_revisions.assert_called_once()


def test_service_codes_found_published_dataset_exists(
    mock_txc_file_attributes_repo,
    mock_revision_repo,
    mock_dataset_repo,
    txc_data,
):
    """
    Service Codes Found and Published Dataset Exists
    """
    mock_txc_file_attributes_repo.get_by_service_code.return_value = [
        OrganisationTXCFileAttributesFactory.create_with_id(
            id_number=111, service_code="SC123", revision_id=1
        ),
        OrganisationTXCFileAttributesFactory.create_with_id(
            id_number=222, service_code="SC456", revision_id=2
        ),
    ]
    mock_revision_repo.get_live_revisions.return_value = [
        OrganisationDatasetRevisionFactory.create_with_id(id_number=1),
        OrganisationDatasetRevisionFactory.create_with_id(id_number=2),
    ]
    mock_dataset_repo.get_published_datasets.return_value = [
        OrganisationDatasetFactory.create_with_id(id_number=100, live_revision_id=1)
    ]
    mock_txc_file_attributes_repo.get_by_revision_id.return_value = [
        OrganisationTXCFileAttributesFactory.create_with_id(
            id_number=111, service_code="SC123", revision_id=1
        ),
        OrganisationTXCFileAttributesFactory.create_with_id(
            id_number=333, service_code="SC777", revision_id=1
        ),
    ]

    with (
        patch(
            "post_schema_check.app.validators.check_service_code_exists.OrganisationTXCFileAttributesRepo",
            return_value=mock_txc_file_attributes_repo,
        ),
        patch(
            "post_schema_check.app.validators.check_service_code_exists.OrganisationDatasetRevisionRepo",
            return_value=mock_revision_repo,
        ),
        patch(
            "post_schema_check.app.validators.check_service_code_exists.OrganisationDatasetRepo",
            return_value=mock_dataset_repo,
        ),
    ):
        result = check_service_code_exists(txc_data, Mock())

        assert len(result) == 1
        assert result[0].is_valid is False
        assert result[0].additional_details.published_dataset == 100  # type: ignore
        assert result[0].additional_details.service_codes[0] in ["SC123", "SC777"]  # type: ignore
        assert result[0].additional_details.service_codes[1] in ["SC123", "SC777"]  # type: ignore


def test_multiple_published_dataset_exists(
    mock_txc_file_attributes_repo,
    mock_revision_repo,
    mock_dataset_repo,
    txc_data,
):
    """
    Service Codes Found and multiple Published Dataset Exists
    """
    mock_txc_file_attributes_repo.get_by_service_code.return_value = [
        OrganisationTXCFileAttributesFactory.create_with_id(
            id_number=111, service_code="SC123", revision_id=1
        ),
        OrganisationTXCFileAttributesFactory.create_with_id(
            id_number=222, service_code="SC456", revision_id=2
        ),
    ]
    mock_revision_repo.get_live_revisions.return_value = [
        OrganisationDatasetRevisionFactory.create_with_id(id_number=1),
        OrganisationDatasetRevisionFactory.create_with_id(id_number=2),
    ]
    mock_dataset_repo.get_published_datasets.return_value = [
        OrganisationDatasetFactory.create_with_id(id_number=100, live_revision_id=1),
        OrganisationDatasetFactory.create_with_id(id_number=200, live_revision_id=2),
    ]
    mock_txc_file_attributes_repo.get_by_revision_id.return_value = [
        OrganisationTXCFileAttributesFactory.create_with_id(
            id_number=111, service_code="SC123", revision_id=1
        ),
        OrganisationTXCFileAttributesFactory.create_with_id(
            id_number=333, service_code="SC777", revision_id=1
        ),
        OrganisationTXCFileAttributesFactory.create_with_id(
            id_number=111, service_code="SC456", revision_id=2
        ),
        OrganisationTXCFileAttributesFactory.create_with_id(
            id_number=333, service_code="SC000", revision_id=2
        ),
    ]

    with (
        patch(
            "post_schema_check.app.validators.check_service_code_exists.OrganisationTXCFileAttributesRepo",
            return_value=mock_txc_file_attributes_repo,
        ),
        patch(
            "post_schema_check.app.validators.check_service_code_exists.OrganisationDatasetRevisionRepo",
            return_value=mock_revision_repo,
        ),
        patch(
            "post_schema_check.app.validators.check_service_code_exists.OrganisationDatasetRepo",
            return_value=mock_dataset_repo,
        ),
    ):
        result = check_service_code_exists(txc_data, Mock())

        assert len(result) == 2
        assert result[0].is_valid is False
        assert result[1].is_valid is False
        assert result[0].additional_details.published_dataset == 100  # type: ignore
        assert result[1].additional_details.published_dataset == 200  # type: ignore
        assert result[0].additional_details.service_codes[0] in ["SC123", "SC777"]  # type: ignore
        assert result[0].additional_details.service_codes[1] in ["SC123", "SC777"]  # type: ignore
        assert result[1].additional_details.service_codes[0] in ["SC456", "SC000"]  # type: ignore
        assert result[1].additional_details.service_codes[1] in ["SC456", "SC000"]  # type: ignore
