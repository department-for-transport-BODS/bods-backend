"""
Functions to load map results
"""

from typing import Literal, overload

from botocore.exceptions import BotoCoreError, ClientError
from common_layer.s3 import S3
from structlog.stdlib import get_logger

from .map_results_manifest import MapResultManifest
from .map_results_models import (
    MapExecutionFailed,
    MapExecutionSucceeded,
    MapResultFailed,
    MapResults,
    MapResultSucceeded,
)

log = get_logger()


@overload
def load_result_file(
    s3_client: S3, file_key: str, result_type: Literal["SUCCEEDED"]
) -> list[MapExecutionSucceeded]: ...


@overload
def load_result_file(
    s3_client: S3, file_key: str, result_type: Literal["FAILED"]
) -> list[MapExecutionFailed]: ...


def load_result_file(
    s3_client: S3, file_key: str, result_type: Literal["SUCCEEDED", "FAILED"]
) -> list[MapExecutionSucceeded] | list[MapExecutionFailed]:
    """Load a single result file using the appropriate model"""
    try:
        with s3_client.get_object(file_key) as file_content:
            json_str = file_content.read().decode("utf-8")

            if result_type == "SUCCEEDED":
                result = MapResultSucceeded.model_validate_json(json_str)
                return result.root
            result = MapResultFailed.model_validate_json(json_str)
            return result.root

    except ClientError:
        log.error(
            "Failed to load result file",
            file_key=file_key,
            result_type=result_type,
            exc_info=True,
        )
        raise
    except BotoCoreError:
        log.error(
            "Boto core error loading result file",
            file_key=file_key,
            result_type=result_type,
            exc_info=True,
        )
        raise


def load_manifest(s3_client: S3, manifest_key: str) -> MapResultManifest:
    """Load and parse the manifest.json file"""

    try:
        with s3_client.get_object(manifest_key) as file_content:
            json_str = file_content.read().decode("utf-8")
            parsed_manifest = MapResultManifest.model_validate_json(json_str)
            log.info(
                "Parsed ResultWriter Manifest",
                manifest_key=manifest_key,
                succeeded=len(parsed_manifest.ResultFiles.SUCCEEDED),
                failed=len(parsed_manifest.ResultFiles.FAILED),
                pending=len(parsed_manifest.ResultFiles.PENDING),
            )
            return parsed_manifest

    except ClientError:
        log.error(
            "Failed to load manifest file", manifest_key=manifest_key, exc_info=True
        )
        raise
    except BotoCoreError:
        log.error(
            "Boto core error loading manifest file",
            manifest_key=manifest_key,
            exc_info=True,
        )
        raise


def load_map_results(
    s3_client: S3,
    map_run_id: str,
) -> MapResults:
    """
    Load both succeeded and failed results using manifest.json to locate files
    """
    manifest = load_manifest(s3_client, map_run_id)

    log.info("Loading Successful Results")
    succeeded_results: list[MapExecutionSucceeded] = []
    for result_file in manifest.ResultFiles.SUCCEEDED:
        results = load_result_file(s3_client, result_file.Key, "SUCCEEDED")
        succeeded_results.extend(results)

        log.info(
            "Loaded succeeded result file",
            key=result_file.Key,
            result_count=len(results),
        )

    log.info("Loading Failed Results")
    failed_results: list[MapExecutionFailed] = []
    for result_file in manifest.ResultFiles.FAILED:
        results = load_result_file(s3_client, result_file.Key, "FAILED")
        failed_results.extend(results)

        log.info(
            "Loaded failed result file", key=result_file.Key, result_count=len(results)
        )

    log.info(
        "Completed loading map results",
        succeeded_count=len(succeeded_results),
        failed_count=len(failed_results),
    )

    return MapResults(
        succeeded=succeeded_results,
        failed=failed_results,
    )


def extract_map_run_id(map_run_arn: str) -> str:
    """
    Extract the Map Run Id from the ARN
    Example ARN: arn:aws:states:region:account:mapRun:state-machine-name/execution-id:map-run-id
    Returns: map-run-id
    """
    try:
        return map_run_arn.split("/")[-1].split(":")[-1]
    except Exception as exc:
        log.error(
            "Failed to extract Map Run Id from ARN",
            map_run_arn=map_run_arn,
            exc_info=True,
        )
        raise ValueError(f"Invalid Map Run ARN format: {map_run_arn}") from exc


def get_map_run_manifest_path(map_run_arn: str, map_run_prefix: str) -> str:
    """
    Generate the S3 Object Path for a Map Run ResultWriter manifest.json
    """
    run_id = extract_map_run_id(map_run_arn)
    manifest_key = f"{map_run_prefix}/{run_id}/manifest.json"
    log.debug("Generated Manifest Key", manifest_key=manifest_key)
    return manifest_key


def get_map_processing_results(
    s3_client: S3, map_run_arn: str, map_run_prefix: str
) -> MapResults:
    """
    Get the Processing Results
    """
    manifest_path = get_map_run_manifest_path(map_run_arn, map_run_prefix)
    map_results = load_map_results(s3_client, manifest_path)
    if map_results.failed:
        log.error(
            "Failed Files in Map",
            failed_files=[f.Name for f in map_results.failed],
        )
    return map_results
