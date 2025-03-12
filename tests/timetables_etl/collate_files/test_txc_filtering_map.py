"""
Map Input Generation Functions
"""

import json
from datetime import datetime

import pytest
from collate_files.app.collate_files import S3FileReference
from collate_files.app.txc_filtering import build_filename_map
from common_layer.aws.step import (
    MapExecutionFailed,
    MapExecutionSucceeded,
    MapInputData,
    MapResults,
    MapRunExecutionStatus,
)


def create_map_input(
    bucket: str | None = None, key: str | None = None, revision_id: int | None = None
) -> "MapInputData":
    """Create a MapInputData object for testing"""
    return MapInputData(
        Bucket=bucket,
        Key=key,
        DatasetRevisionId=revision_id,
        mapDatasetEtlTaskResultId=1,
    )


def create_map_execution_succeeded(
    execution_arn: str = "arn:aws:states:test-arn",
    bucket: str | None = None,
    key: str | None = None,
    revision_id: int | None = None,
) -> "MapExecutionSucceeded":
    """Create a MapExecutionSucceeded object for testing"""

    input_data = create_map_input(bucket, key, revision_id)

    input_json = json.dumps(
        {
            "mapS3Bucket": bucket,
            "mapS3Object": key,
            "mapDatasetRevisionId": revision_id,
            "mapDatasetEtlTaskResultId": 1,
        }
    )

    # Create a map execution with parsed input
    execution = MapExecutionSucceeded(
        ExecutionArn=execution_arn,
        Input=input_json,  # Use the valid JSON here
        InputDetails={},
        Name="test-execution",
        OutputDetails={},
        RedriveCount=0,
        RedriveStatus="NOT_REDRIVABLE",
        StartDate=datetime.now(),
        StateMachineArn="arn:aws:states:test-arn",
        StopDate=datetime.now(),
        Status=MapRunExecutionStatus.SUCCEEDED,
        Output="{}",
        RedriveStatusReason="None",
        parsed_input=input_data,
    )

    return execution


def create_map_results(
    successful_executions: list[MapExecutionSucceeded] | None = None,
    failed_executions: list[MapExecutionFailed] | None = None,
) -> "MapResults":
    """Create a MapResults object for testing"""
    return MapResults(
        succeeded=successful_executions or [], failed=failed_executions or []
    )


def create_s3_file_reference(
    bucket: str, object_key: str, superceded: bool, etl_id: int
) -> "S3FileReference":
    """Create an S3FileReference object for testing"""
    return S3FileReference(
        bucket=bucket,
        object=object_key,
        superceded_file=superceded,
        fileAttributesEtl=etl_id,
    )


@pytest.mark.parametrize(
    "map_results, expected_filenames",
    [
        pytest.param(
            create_map_results(
                successful_executions=[
                    create_map_execution_succeeded(
                        execution_arn="arn:aws:states:arn1",
                        bucket="test-bucket",
                        key="folder/file1.xml",
                        revision_id=100,
                    ),
                    create_map_execution_succeeded(
                        execution_arn="arn:aws:states:arn2",
                        bucket="test-bucket",
                        key="folder/file2.xml",
                        revision_id=100,
                    ),
                    create_map_execution_succeeded(
                        execution_arn="arn:aws:states:arn3",
                        bucket="test-bucket",
                        key="folder/subfolder/file3.xml",
                        revision_id=100,
                    ),
                ]
            ),
            ["file1.xml", "file2.xml", "file3.xml"],
            id="Multiple executions",
        ),
        pytest.param(
            create_map_results(
                successful_executions=[
                    create_map_execution_succeeded(
                        execution_arn="arn:aws:states:arn1",
                        bucket="test-bucket",
                        key=None,
                        revision_id=100,
                    ),
                ]
            ),
            [],
            id="Execution with None key",
        ),
        pytest.param(
            create_map_results(
                successful_executions=[
                    MapExecutionSucceeded(
                        ExecutionArn="arn:aws:states:test-arn",
                        Input="{}",
                        InputDetails={},
                        Name="test-execution",
                        OutputDetails={},
                        RedriveCount=0,
                        RedriveStatus="NOT_REDRIVABLE",
                        StartDate=datetime.now(),
                        StateMachineArn="arn:aws:states:test-arn",
                        StopDate=datetime.now(),
                        Status=MapRunExecutionStatus.SUCCEEDED,
                        Output="{}",
                        RedriveStatusReason="None",
                        parsed_input=None,
                    )
                ]
            ),
            [],
            id="Execution with None parsed_input",
        ),
        pytest.param(
            create_map_results(),
            [],
            id="Empty map results",
        ),
    ],
)
def test_build_filename_map(
    map_results: MapResults,
    expected_filenames: list[str],
):
    """
    Test building a filename map from map results
    """
    result = build_filename_map(map_results)

    assert set(result.keys()) == set(expected_filenames)

    for filename, execution in result.items():
        assert execution.parsed_input and execution.parsed_input.Key
        assert execution.parsed_input.Key.endswith(filename)
