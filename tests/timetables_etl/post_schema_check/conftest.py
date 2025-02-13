"""
Mock Fixtures
"""

from unittest.mock import create_autospec

import pytest
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRepo,
    OrganisationDatasetRevisionRepo,
    OrganisationTXCFileAttributesRepo,
)


@pytest.fixture
def mock_txc_file_attributes_repo() -> OrganisationTXCFileAttributesRepo:
    """
    Mock Repo
    """
    return create_autospec(OrganisationTXCFileAttributesRepo, instance=True)


@pytest.fixture
def mock_revision_repo() -> OrganisationDatasetRevisionRepo:
    """
    Mock Repo
    """
    return create_autospec(OrganisationDatasetRevisionRepo, instance=True)


@pytest.fixture
def mock_dataset_repo() -> OrganisationDatasetRepo:
    """
    Mock Repo
    """
    return create_autospec(OrganisationDatasetRepo, instance=True)
