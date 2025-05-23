"""
Description: Module contains the database functionality for
             FileProcessingResult table
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Literal, TypeVar
from uuid import uuid4

from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database.client import SqlDB
from common_layer.database.models import (
    ETLErrorCode,
    FileProcessingResult,
    PipelineErrorCode,
    PipelineProcessingStep,
    TaskState,
)
from common_layer.database.repos import (
    FileProcessingResultRepo,
    PipelineErrorCodeRepository,
    PipelineProcessingStepRepository,
)
from common_layer.database.repos.operation_decorator import SQLDBClientError
from common_layer.db.constants import StepName
from common_layer.exceptions import ETLException
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

log = get_logger()


def map_exception_to_error_code(exception: Exception) -> ETLErrorCode:
    """
    Maps exceptions to corresponding ETL error codes.
    """

    if isinstance(exception, ETLException):
        return exception.code
    return ETLErrorCode.SYSTEM_ERROR


def get_file_processing_error_code(
    db: SqlDB, status: ETLErrorCode
) -> PipelineErrorCode | None:
    """
    Retrieves the error code object for a given status.
    """
    return PipelineErrorCodeRepository(db).get_or_create_by_error_code(status)


def get_or_create_step(db: SqlDB, name: str, category: str) -> PipelineProcessingStep:
    """
    Gets an existing processing step or creates it if it doesn't exist.
    """
    repo = PipelineProcessingStepRepository(db)
    return repo.get_or_create_by_name_and_category(name, category)


def get_dataset_type(event: dict[str, str]) -> Literal["TIMETABLES", "FARES"]:
    """
    Get the type of dataset from the event
    """
    dataset_type = event.get("DatasetType", "TIMETABLES")
    return "TIMETABLES" if "timetable" in dataset_type.lower() else "FARES"


T = TypeVar("T")  # Return type of the wrapped function


@dataclass
class ProcessingContext:
    """Context for the file processing operation"""

    task_id: str
    step_name: StepName
    db: SqlDB | None = None
    processing_result: FileProcessingResult | None = None


def get_object_key(event: dict[str, str]) -> str:
    """Extracts filename from event's ObjectKey, falling back to UNKNOWN if unavailable."""
    object_key = event.get("ObjectKey")
    if not object_key:
        log.warning("Could not determine Filename from ObjectKey")
        return "UNKNOWN"
    try:
        return object_key.split("/")[-1]
    except (AttributeError, IndexError):
        return object_key


def get_revision_id(event: dict[str, str | int]) -> int:
    """Extracts revision ID from event, trying both casing variants."""
    revision_id = event.get("datasetRevisionId") or event.get("DatasetRevisionId")
    if revision_id is None:
        raise ValueError("No revision ID found in event")
    try:
        return int(revision_id)
    except ValueError as exc:
        raise ValueError(
            f"Revision ID '{revision_id}' could not be converted to integer"
        ) from exc


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
            filename=get_object_key(event),
            pipeline_processing_step_id=step.id,
            revision_id=get_revision_id(event),
            error_message="",
            pipeline_error_code_id=None,
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


def write_error_to_db(
    db: SqlDB, processing_result: FileProcessingResult, exception: Exception
):
    """
    Update the FileProcessingResult with the error returned by the lambda
    """
    error_status = map_exception_to_error_code(exception)
    error_code = get_file_processing_error_code(db, error_status)

    processing_result.status = TaskState.FAILURE
    processing_result.completed = datetime.now(UTC)

    if error_code is None:
        processing_result.pipeline_error_code_id = None
        log.warning("Error Code was not found in DB, setting to NULL")
    else:
        processing_result.pipeline_error_code_id = error_code.id

    FileProcessingResultRepo(db).update(processing_result)


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
    else:
        log.warning(
            "Database Connection not available, cannot update FileProcessingResult"
        )


def file_processing_result_to_db(step_name: StepName):
    """
    Decorator to create a DatasetETLTaskResult with structured logging
    """

    def decorator(
        func: Callable[[dict[str, Any], LambdaContext], T],
    ) -> Callable[[dict[str, Any], LambdaContext], T]:
        def wrapper(event: dict[str, Any], context: LambdaContext) -> T:
            configure_logging(event, context)
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

            except ETLException as validation_error:
                handle_lambda_error(processing_context, validation_error)
                log.error(
                    "Input File Failed Step",
                    error_type=validation_error.__class__.__name__,
                    error_message=validation_error.to_dict(),
                    step_name=step_name.value,
                    exc_info=True,
                )

                raise

            except Exception as lambda_error:  # pylint: disable=broad-exception-caught
                handle_lambda_error(processing_context, lambda_error)

                if isinstance(lambda_error, SQLDBClientError):
                    error_message = lambda_error.to_dict()
                else:
                    error_message = str(lambda_error)
                log.critical(
                    "Lambda Raised Unhandled Exception",
                    error_type=lambda_error.__class__.__name__,
                    error_message=error_message,
                    step_name=step_name.value,
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator
