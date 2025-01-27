"""
Mock Fixtures
"""

from unittest.mock import create_autospec

import pytest
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo,
)


@pytest.fixture
def mock_revision_repo() -> OrganisationDatasetRevisionRepo:
    """
    Mock Repo
    """
    return create_autospec(OrganisationDatasetRevisionRepo, instance=True)
