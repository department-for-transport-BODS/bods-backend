"""
Fixtures for DownloadDataset
"""

import zipfile
from io import BytesIO

import pytest
from common_layer.database.models.model_organisation import OrganisationDatasetRevision
from download_dataset.app.file_download import FileDownloader

from tests.factories.database.organisation import OrganisationDatasetRevisionFactory


@pytest.fixture
def mock_revision() -> OrganisationDatasetRevision:
    """Fixture for creating a mock revision"""
    return OrganisationDatasetRevisionFactory.create(
        url_link="https://example.com/data.csv"
    )


@pytest.fixture
def mock_file_downloader():
    """
    Mock FileDownloader instance
    """
    return FileDownloader()


def create_valid_zip() -> bytes:
    """
    Return Bytes of a Valid Zip
    """
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_STORED) as zip_file:
        zip_file.writestr("test.txt", "This is a test file.")
    zip_buffer.seek(0)
    return zip_buffer.read()
