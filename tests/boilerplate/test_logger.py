from boilerplate.logger import (
    get_dataset_adapter_from_revision,
    DatasetPipelineLoggerContext,
)


def test_get_dataset_adapter_from_revision(caplog):
    revision_id = 1
    dataset_id = 2
    expected_logger_context = DatasetPipelineLoggerContext(
        component_name="TimetablePipeline",
        class_name="Dataset",
        revision_id=1,
        object_id=2,
    )
    logger = get_dataset_adapter_from_revision(revision_id, dataset_id)

    assert logger.extra == {"context": expected_logger_context}
    logger.info("Test Logger Call")
    assert len(caplog.records) == 1
    assert caplog.records[0].message == "[TimetablePipeline] Dataset 2 (Revision 1) => Test Logger Call"
