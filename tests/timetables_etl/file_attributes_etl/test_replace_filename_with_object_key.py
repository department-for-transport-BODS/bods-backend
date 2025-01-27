"""
Test that the temporary file name usage for TXCFileAttributes is working correctly
"""

from datetime import date

import pytest
from common_layer.database.models.model_organisation import (
    OrganisationTXCFileAttributes,
)
from file_attributes_etl.app.file_attributes_etl import replace_filename_with_object_key

from tests.factories.database.organisation import OrganisationTXCFileAttributesFactory


@pytest.fixture(name="file_attributes_fixture")
def default_file_attributes() -> OrganisationTXCFileAttributes:
    """Fixture providing default file attributes for testing.

    Returns:
        OrganisationTXCFileAttributes: Default file attributes
    """
    return OrganisationTXCFileAttributesFactory.with_service_details(
        origin="London",
        destination="Manchester",
        line_names=["Test Line 1"],
        operating_period_start_date=date(2024, 1, 1),
        operating_period_end_date=date(2024, 12, 31),
    )


@pytest.mark.parametrize(
    "s3_key,expected_filename",
    [
        pytest.param(
            "subfolder/test_file.xml",
            "test_file.xml",
            id="Valid S3 Key With Subfolder",
        ),
        pytest.param(
            "direct_file.xml",
            "direct_file.xml",
            id="Valid S3 Key Without Subfolder",
        ),
        pytest.param(
            "deep/nested/path/complex_file.xml",
            "complex_file.xml",
            id="Valid S3 Key With Deep Nesting",
        ),
    ],
)
def test_replace_filename_with_object_key_updates_filename(
    file_attributes_fixture: OrganisationTXCFileAttributes,
    s3_key: str,
    expected_filename: str,
) -> None:
    """Test replace_filename_with_object_key function successfully updates filename."""
    result = replace_filename_with_object_key(file_attributes_fixture, s3_key)
    assert result.filename == expected_filename


@pytest.mark.parametrize(
    "s3_key,expected_error",
    [
        pytest.param(
            None,
            id="None for File Key",
        ),
        pytest.param(
            "",
            id="Empty S3 Key Should Keep Original Filename",
        ),
    ],
)
def test_replace_filename_with_object_key_keeps_original(
    file_attributes_fixture: OrganisationTXCFileAttributes,
    s3_key: str,
) -> None:
    """Test replace_filename_with_object_key function keeps original filename in error cases."""
    original_filename = file_attributes_fixture.filename

    result = replace_filename_with_object_key(file_attributes_fixture, s3_key)
    assert result.filename == original_filename
