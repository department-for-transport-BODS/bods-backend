"""
Description: Module contains the database functionality for
             FileProcessingResult table
"""

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from common_layer.database.client import SqlDB
from common_layer.database.models.model_pipelines import (
    ETLErrorCode,
    FileProcessingResult,
    PipelineErrorCode,
    PipelineProcessingStep,
    TaskState,
)
from common_layer.database.repos.repo_etl_task import (
    FileProcessingResultRepo,
    PipelineErrorCodeRepository,
    PipelineProcessingStepRepository,
)
from common_layer.db.constants import StepName
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

log = get_logger()


def map_exception_to_error_code(exception) -> ETLErrorCode:
    """
    Maps exceptions to corresponding ETL error codes.
    """
    exception_mapping = {
        "ClamConnectionError": ETLErrorCode.AV_CONNECTION_ERROR,
        "SuspiciousFile": ETLErrorCode.SUSPICIOUS_FILE,
        "AntiVirusError": ETLErrorCode.ANTIVIRUS_FAILURE,
        "NestedZipForbidden": ETLErrorCode.NESTED_ZIP_FORBIDDEN,
        "ZipTooLarge": ETLErrorCode.ZIP_TOO_LARGE,
        "NoDataFound": ETLErrorCode.NO_DATA_FOUND,
        "FileTooLarge": ETLErrorCode.FILE_TOO_LARGE,
        "XMLSyntaxError": ETLErrorCode.XML_SYNTAX_ERROR,
        "DangerousXML": ETLErrorCode.DANGEROUS_XML_ERROR,
        "NoSchemaDefinition": ETLErrorCode.SCHEMA_VERSION_MISSING,
        "NoRowFound": ETLErrorCode.NO_VALID_FILE_TO_PROCESS,
    }
    return exception_mapping.get(
        exception.__class__.__name__, ETLErrorCode.SUSPICIOUS_FILE
    )


def get_file_processing_error_code(
    db: SqlDB, status: ETLErrorCode
) -> PipelineErrorCode | None:
    """
    Retrieves the error code object for a given status.
    """
    return PipelineErrorCodeRepository(db).get_by_error_code(status)


def write_error_to_db(db: SqlDB, processing_result: FileProcessingResult, exception):
    """
    Update the FileProcessingResult with the error returned by the lambda
    """
    error_status = map_exception_to_error_code(exception)
    error_code = get_file_processing_error_code(db, error_status)

    processing_result.status = TaskState.FAILURE
    processing_result.completed = datetime.now(UTC)
    if error_code is None:
        log.warning("Error Code was not found in DB, defaulting to 1")
    processing_result.pipeline_error_code_id = 1
    FileProcessingResultRepo(db).update(processing_result)


def get_or_create_step(db: SqlDB, name: str, category: str) -> PipelineProcessingStep:
    """
    Gets an existing processing step or creates it if it doesn't exist.
    """
    repo = PipelineProcessingStepRepository(db)
    return repo.get_or_create_by_name_and_category(name, category)


def get_dataset_type(event: dict) -> Literal["TIMETABLES", "FARES"]:
    """
    Get the type of dataset from the event
    """
    dataset_type = event.get("DatasetType", "TIMETABLES")
    return "TIMETABLES" if dataset_type.startswith("timetable") else "FARES"


def file_processing_result_to_db(step_name: StepName):
    """
    Decorator to create a DatasetETLTaskResult
    """

    def decorator(func):
        def wrapper(event, context):
            db = None
            task_id = str(uuid4())
            processing_result = None
            result = None
            error_occurred = False
            configure_logging()
            # Attempt to set up before executing the lambda function
            try:
                log.info("Processing Step", step_name=step_name, input_data=event)
                db = SqlDB()
                step = get_or_create_step(db, step_name.value, get_dataset_type(event))
                processing_result = FileProcessingResult(
                    task_id=task_id,
                    status=TaskState.STARTED,
                    filename=event["ObjectKey"].split("/")[-1],
                    pipeline_processing_step_id=step.id,
                    revision_id=event["datasetRevisionId"],
                    error_message="",
                    pipeline_error_code_id=0,
                )
                processing_result = FileProcessingResultRepo(db).insert(
                    processing_result
                )
            except Exception as setup_error:  # pylint: disable=broad-exception-caught
                log.error("An Exception Occurred During Setup", exc_info=True)
                error_occurred = True
                if db is not None and processing_result is not None:
                    write_error_to_db(db, processing_result, setup_error)

            # Execute the lambda function regardless of setup success
            try:
                result = func(event, context)
                log.info("Lambda Returned", result=result)
            except Exception as lambda_error:  # pylint: disable=broad-exception-caught
                log.error(
                    "An Exception Occurred During Lambda Execution", exc_info=True
                )
                error_occurred = True
                if db is not None and processing_result is not None:
                    write_error_to_db(db, processing_result, lambda_error)

            # Attempt to tear down after executing the lambda function
            try:
                if db is not None and processing_result is not None:
                    processing_result.status = (
                        TaskState.FAILURE if error_occurred else TaskState.SUCCESS
                    )
                    processing_result.completed = datetime.now(UTC)
                    FileProcessingResultRepo(db).update(processing_result)
            except (
                Exception  # pylint: disable=broad-exception-caught
            ) as teardown_error:
                log.error("An Exception Occurred During Teardown", exc_info=True)
                if db is not None and processing_result is not None:
                    write_error_to_db(db, processing_result, teardown_error)

            return result

        return wrapper

    return decorator
