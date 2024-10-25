from src.boilerplate.logger import get_dataset_adapter_from_revision, DatasetPipelineLoggerContext
from unittest.mock import MagicMock


def test_get_dataset_adapter_from_revision():
    revision = MagicMock(id=1, dataset_id=2)
    expected_logger_context = DatasetPipelineLoggerContext(component_name='TimetablePipeline', class_name='Dataset', revision_id=1, object_id=2)
    logger = get_dataset_adapter_from_revision(revision)
    assert logger.extra == {
        "context": expected_logger_context
    }