"""
Description: Module contains the database functionality for
             FileProcessingResult table
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Literal, TypeVar
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


T = TypeVar("T")  # Return type of the wrapped function
Context = TypeVar("Context")  # AWS Lambda context type


@dataclass
class ProcessingContext:
    """Context for the file processing operation"""

    task_id: str
    step_name: StepName
    db: SqlDB | None = None
    processing_result: FileProcessingResult | None = None


def initialize_processing(
    event: dict[str, Any],
    step_name: StepName,
) -> ProcessingContext:
    """Initialize the processing context with database connection and task"""
    task_id = str(uuid4())
    context = ProcessingContext(task_id=task_id, step_name=step_name)

    try:
        db = SqlDB()
        step = get_or_create_step(db, step_name.value, get_dataset_type(event))
        processing_result = FileProcessingResult(
            task_id=str(task_id),
            status=TaskState.STARTED,
            filename=event["ObjectKey"].split("/")[-1],
            pipeline_processing_step_id=step.id,
            revision_id=event["datasetRevisionId"],
            error_message="",
            pipeline_error_code_id=0,
        )
        context.db = db
        context.processing_result = FileProcessingResultRepo(db).insert(
            processing_result
        )

    except Exception as setup_error:  # pylint: disable=broad-exception-caught
        log.error(
            "Database Setup Failed",
            error_type=setup_error.__class__.__name__,
            error_message=str(setup_error),
            step_name=step_name.value,
            task_id=str(task_id),
            exc_info=True,
        )
        # Return context without DB connection - lambda will still execute
        return context

    return context


def handle_lambda_success(context: ProcessingContext) -> None:
    """Handle successful lambda execution by updating database"""
    if context.db is not None and context.processing_result is not None:
        try:
            context.processing_result.status = TaskState.SUCCESS
            context.processing_result.completed = datetime.now(UTC)
            FileProcessingResultRepo(context.db).update(context.processing_result)
        except Exception as teardown_error:  # pylint: disable=broad-exception-caught
            log.error(
                "Failed to Update Database with Success Result",
                error_type=teardown_error.__class__.__name__,
                error_message=str(teardown_error),
                step_name=context.step_name.value,
                task_id=str(context.task_id),
                exc_info=True,
            )


def handle_lambda_error(context: ProcessingContext, error: Exception) -> None:
    """Handle lambda execution failure by updating database"""
    if context.db is not None and context.processing_result is not None:
        try:
            write_error_to_db(context.db, context.processing_result, error)
        except Exception as db_error:  # pylint: disable=broad-exception-caught
            log.error(
                "Failed to Write Error to Database",
                error_type=db_error.__class__.__name__,
                error_message=str(db_error),
                step_name=context.step_name.value,
                task_id=str(context.task_id),
                exc_info=True,
            )


def file_processing_result_to_db(step_name: StepName):
    """
    Decorator to create a DatasetETLTaskResult with structured logging
    """

    def decorator(func: Callable[[dict, Context], T]) -> Callable[[dict, Context], T]:
        def wrapper(event: dict, context: Context) -> T:
            configure_logging()
            processing_context = initialize_processing(event, step_name)

            try:
                # Execute the lambda function regardless of DB connection status
                result = func(event, context)
                log.info("Lambda Execution Complete", result=result)

                # Only attempt to update DB if connection exists
                if (
                    processing_context.db is not None
                    and processing_context.processing_result is not None
                ):
                    handle_lambda_success(processing_context)
                else:
                    log.warning(
                        "Database Connection not available, cannot update FileProcessingResult"
                    )
                return result

            except Exception as lambda_error:  # pylint: disable=broad-exception-caught
                log.error(
                    "Lambda Execution Failed",
                    error_type=lambda_error.__class__.__name__,
                    error_message=str(lambda_error),
                    step_name=step_name.value,
                    task_id=str(processing_context.task_id),
                    exc_info=True,
                )
                # Only attempt to write error to DB if connection exists
                if (
                    processing_context.db is not None
                    and processing_context.processing_result is not None
                ):
                    handle_lambda_error(processing_context, lambda_error)
                else:
                    log.warning(
                        "Database Connection not available, cannot update FileProcessingResult"
                    )
                raise

        return wrapper

    return decorator
