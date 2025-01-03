"""
Tests for the file_processing_result_to_db decorator
Used to update task status in the lambdas
"""

from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from common_layer.database.models.model_pipelines import (
    ETLErrorCode,
    PipelineErrorCode,
    PipelineProcessingStep,
    TaskState,
)
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import (
    file_processing_result_to_db,
    get_dataset_type,
    get_file_processing_error_code,
    get_or_create_step,
    handle_lambda_error,
    handle_lambda_success,
    initialize_processing,
    map_exception_to_error_code,
    write_error_to_db,
)

from tests.factories.database.pipelines import (
    FileProcessingResultFactory,
    PipelineErrorCodeFactory,
)


@pytest.mark.parametrize(
    "exception_class,expected_code",
    [
        pytest.param(
            "ClamConnectionError",
            ETLErrorCode.AV_CONNECTION_ERROR,
            id="Map Antivirus Connection Error",
        ),
        pytest.param(
            "SuspiciousFile",
            ETLErrorCode.SUSPICIOUS_FILE,
            id="Map Suspicious File Error",
        ),
        pytest.param(
            "AntiVirusError",
            ETLErrorCode.ANTIVIRUS_FAILURE,
            id="Map Antivirus Failure",
        ),
        pytest.param(
            "NestedZipForbidden",
            ETLErrorCode.NESTED_ZIP_FORBIDDEN,
            id="Map Nested Zip Error",
        ),
        pytest.param(
            "UnknownError",
            ETLErrorCode.SUSPICIOUS_FILE,
            id="Map Unknown Error To Default",
        ),
    ],
)
def test_map_exception_to_error_code(exception_class, expected_code):
    """
    Map the Python exceptions to the DB Statuses
    """
    exception = type(exception_class, (Exception,), {})()

    result = map_exception_to_error_code(exception)

    assert result == expected_code


@pytest.mark.parametrize(
    "dataset_type,expected_category",
    [
        pytest.param(
            "timetables",
            "TIMETABLES",
            id="Timetables Dataset Type",
        ),
        pytest.param(
            "timetables_v1",
            "TIMETABLES",
            id="Timetables With Version",
        ),
        pytest.param(
            "fares",
            "FARES",
            id="Fares Dataset Type",
        ),
        pytest.param(
            None,
            "TIMETABLES",
            id="Default Dataset Type",
        ),
    ],
)
def test_get_dataset_type(dataset_type, expected_category):
    """
    Get the correct dataset type
    """
    event = {}
    if dataset_type:
        event["DatasetType"] = dataset_type

    result = get_dataset_type(event)

    assert result == expected_category


@pytest.mark.parametrize(
    "step_exists,name,category",
    [
        pytest.param(
            True,
            "validate_xml",
            "TIMETABLES",
            id="Get Existing Step",
        ),
        pytest.param(
            False,
            "new_step",
            "FARES",
            id="Create New Step",
        ),
    ],
)
def test_get_or_create_step(step_exists, name, category):
    """Test getting or creating a pipeline processing step"""
    db = MagicMock()
    mock_repo = MagicMock()
    step = PipelineProcessingStep(name=name, category=category)

    with patch(
        "common_layer.database.repos.repo_etl_task.PipelineProcessingStepRepository",
        return_value=mock_repo,
    ):
        mock_repo.get_by_name.return_value = step if step_exists else None
        mock_repo.insert.return_value = step
        result = get_or_create_step(db, name, category)

        assert result.name == name
        assert result.category == category


def test_initialize_processing():
    """
    Tests the creation of the initial task data
    """
    event = {
        "ObjectKey": "test/file.xml",
        "datasetRevisionId": 123,
        "DatasetType": "timetables",
    }

    with patch("common_layer.database.client.SqlDB") as mock_db:
        context = initialize_processing(event, StepName.CLAM_AV_SCANNER)

    assert context is not None
    assert isinstance(context.task_id, str)
    assert UUID(context.task_id)
    assert context.step_name == StepName.CLAM_AV_SCANNER


def test_initialize_processing_db_failure():
    """
    Test when the DB could not be created
    """
    event = {
        "ObjectKey": "test/file.xml",
        "datasetRevisionId": 123,
        "DatasetType": "timetables",
    }

    with patch("common_layer.database.client.SqlDB", side_effect=Exception("DB Error")):
        context = initialize_processing(event, StepName.CLAM_AV_SCANNER)

    assert context is not None
    assert context.db is None
    assert context.processing_result is None


@pytest.mark.parametrize(
    "has_db_connection",
    [
        pytest.param(True, id="With Database Connection"),
        pytest.param(False, id="Without Database Connection"),
    ],
)
def test_handle_lambda_success(has_db_connection):
    """
    Test for sucessfully creating a lambda
    """
    db = MagicMock() if has_db_connection else None
    processing_result = FileProcessingResultFactory() if has_db_connection else None
    context = MagicMock(
        db=db,
        processing_result=processing_result,
        step_name=StepName.CLAM_AV_SCANNER,
        task_id=str(UUID(bytes=b"1" * 16)),
    )

    handle_lambda_success(context)

    if has_db_connection:
        assert context.processing_result.status == TaskState.SUCCESS
        assert context.processing_result.completed is not None


@pytest.mark.parametrize(
    "exception_type,has_db_connection",
    [
        pytest.param(
            "XMLSyntaxError",
            True,
            id="XML Error With DB",
        ),
        pytest.param(
            "FileTooLarge",
            True,
            id="File Size Error With DB",
        ),
        pytest.param(
            "XMLSyntaxError",
            False,
            id="XML Error Without DB",
        ),
    ],
)
def test_handle_lambda_error(exception_type, has_db_connection):
    db = MagicMock() if has_db_connection else None
    processing_result = FileProcessingResultFactory() if has_db_connection else None
    context = MagicMock(
        db=db,
        processing_result=processing_result,
        step_name=StepName.CLAM_AV_SCANNER,
        task_id=str(UUID(bytes=b"1" * 16)),
    )
    error = type(exception_type, (Exception,), {})()

    handle_lambda_error(context, error)

    if has_db_connection:
        assert context.processing_result.status == TaskState.FAILURE
        assert context.processing_result.completed is not None


@pytest.mark.parametrize(
    "success,db_available",
    [
        pytest.param(True, True, id="Success With DB"),
        pytest.param(True, False, id="Success Without DB"),
        pytest.param(False, True, id="Failure With DB"),
        pytest.param(False, False, id="Failure Without DB"),
    ],
)
def test_file_processing_result_to_db_decorator(success, db_available):
    """
    Test the decorator
    """
    event = {
        "ObjectKey": "test/file.xml",
        "datasetRevisionId": 123,
        "DatasetType": "timetables",
    }
    context = MagicMock()

    @file_processing_result_to_db(step_name=StepName.CLAM_AV_SCANNER)
    def test_lambda(event, context):
        if not success:
            raise ValueError("Test error")
        return "success"

    # Mock DB connection based on db_available
    db_patch = patch("common_layer.database.client.SqlDB")
    if not db_available:
        db_patch.side_effect = Exception("DB connection failed")  # type: ignore

    with db_patch:
        if success:
            result = test_lambda(event, context)
            assert result == "success"
        else:
            with pytest.raises(ValueError):
                test_lambda(event, context)
