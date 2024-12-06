import pytest
from unittest.mock import MagicMock, patch
from enums import FeedStatus
from exceptions.pipeline_exceptions import PipelineException

from db.repositories.dataset_revision import (
    DatasetRevisionRepository,
    update_file_hash_in_db
)
from tests.mock_db import MockedDB, organisation_datasetrevision



def test_get_by_id():
    mock_db = MockedDB()

    dataset_revision_id = 123
    dataset_revision = organisation_datasetrevision(
        id=dataset_revision_id,
        status=FeedStatus.pending
    )
    with mock_db.session as session:
        session.add(dataset_revision)
        session.commit()

    repo = DatasetRevisionRepository(mock_db)
    result = repo.get_by_id(dataset_revision_id)

    assert result.id == dataset_revision_id
    assert result.status == FeedStatus.pending


def test_get_by_id_not_found():
    mock_db = MockedDB()
    repo = DatasetRevisionRepository(mock_db)
    with pytest.raises(PipelineException, match="DatasetRevision 999 does not exist."):
        repo.get_by_id(999)


def test_update():
    mock_db = MockedDB()

    dataset_revision_id = 123
    dataset_revision = organisation_datasetrevision(
        id=dataset_revision_id,
        status=FeedStatus.pending
    )
    with mock_db.session as session:
        session.add(dataset_revision)
        session.commit()

    repo = DatasetRevisionRepository(mock_db)
    
    dataset_revision.status = FeedStatus.error
    repo.update(dataset_revision)

    updated_revision = repo.get_by_id(dataset_revision_id)
    assert updated_revision.id == dataset_revision_id
    assert updated_revision.status == FeedStatus.error


def test_update_exception():
    mock_db = MockedDB()

    mock_session = MagicMock()
    mock_session.__enter__.return_value.commit.side_effect = Exception("Error saving changes")
    mock_db.session = mock_session

    updated_record = MagicMock()
    repo = DatasetRevisionRepository(mock_db)

    with pytest.raises(PipelineException, match="Failed to update DatasetRevision: Error saving changes"):
        repo.update(updated_record)

    mock_session.__enter__.return_value.rollback.assert_called_once(), "session rollback should be called"
