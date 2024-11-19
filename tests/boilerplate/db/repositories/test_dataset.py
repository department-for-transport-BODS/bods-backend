
import pytest
from db.repositories.dataset import DatasetRepository
from exceptions.pipeline_exceptions import PipelineException
from tests.mock_db import MockedDB, organisation_dataset


def test_get_by_id():
    mock_db = MockedDB()

    dataset_id = 123
    dataset = organisation_dataset(
        id=dataset_id,
    )
    with mock_db.session as session:
        session.add(dataset)
        session.commit()

    repo = DatasetRepository(mock_db)
    result = repo.get_by_id(dataset_id)

    assert result.id == dataset_id


def test_get_by_id_not_found():
    mock_db = MockedDB()
    repo = DatasetRepository(mock_db)
    with pytest.raises(PipelineException, match="Dataset 999 does not exist."):
        repo.get_by_id(999)
