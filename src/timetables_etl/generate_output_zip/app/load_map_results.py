"""
Functions to load map results
"""

import json
from enum import Enum
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError
from common_layer.s3 import S3
from structlog.stdlib import get_logger

from .models import ResultFile

log = get_logger()


class ResultType(str, Enum):
    """Valid result types for Step Functions Map state"""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    PENDING = "PENDING"


def validate_result_type(result_type: str | ResultType) -> ResultType:
    """Validate and convert input to ResultType enum"""
    if isinstance(result_type, ResultType):
        return result_type
    try:
        return ResultType(result_type.upper())
    except ValueError as e:
        log.error(
            "Invalid result type provided",
            ResultType=result_type,
            ValidTypes=[t.value for t in ResultType],
        )
        raise ValueError(f"Invalid result type: {result_type}") from e


def get_result_file_path(
    base_path: str, result_type: ResultType, file_index: int
) -> str:
    """Create the S3 key for a specific result file"""
    return f"{base_path}/{result_type}_{file_index}.json"


def load_single_result_file(
    s3_client: S3, file_key: str
) -> tuple[list[dict[str, Any]], bool]:
    """
    Load and parse a single result file,
    returning the parsed data and whether to continue loading"""
    try:
        file_content = s3_client.get_object(file_key)
        result_data: list[dict[str, Any]] = json.loads(
            file_content.read().decode("utf-8")
        )

        if not result_data:
            log.warning("Empty result file found", FilePath=file_key)
            return [], True

        return result_data, True

    except (ClientError, BotoCoreError) as e:
        if isinstance(e, ClientError):
            return [], False
        log.error(
            "Error loading result file",
            FilePath=file_key,
            Error=str(e),
            exc_info=True,
        )
        raise


def log_multiple_files(
    result_type: ResultType, file_index: int, file_key: str, result_count: int
) -> None:
    """Log a critical message when multiple result files are detected"""
    if file_index > 0:
        log.critical(
            "Multiple result files detected",
            FileType=result_type.value,
            FileIndex=file_index,
            FilePath=file_key,
            ResultCount=result_count,
        )


def parse_result_file(raw_results: list[dict[str, Any]]) -> list[ResultFile]:
    """Convert raw result data into ResultFile objects"""
    try:
        return [
            ResultFile.model_validate({"Key": item["Key"], "Size": item["Size"]})
            for item in raw_results
        ]
    except KeyError as e:
        raise ValueError(f"Missing required field in result data: {e}")


def load_result_files(
    s3_client: S3,
    output_prefix: str,
    map_run_id: str,
    result_type: ResultType | str,
) -> list[ResultFile]:
    """Load and combine all result files of the specified type from Step Functions Map state"""
    result_type_enum = validate_result_type(result_type)
    base_path = f"{output_prefix}/tt-etl-map-results/{map_run_id}"
    aggregated_results: list[dict[str, Any]] = []

    log.info(
        "Starting to load result files",
        ResultType=result_type_enum.value,
        BasePath=base_path,
    )

    for file_index in range(100):
        file_key = get_result_file_path(base_path, result_type_enum, file_index)
        results, should_continue = load_single_result_file(s3_client, file_key)

        if results:
            aggregated_results.extend(results)
            log_multiple_files(result_type_enum, file_index, file_key, len(results))

        if not should_continue:
            break

    log.info(
        "Completed loading result files",
        ResultType=result_type_enum.value,
        TotalResults=len(aggregated_results),
    )

    return parse_result_file(aggregated_results)
