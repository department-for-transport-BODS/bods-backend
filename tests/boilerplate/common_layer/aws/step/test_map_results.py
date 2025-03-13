"""
Map Results Tests
"""

import pytest
from common_layer.aws.step import (
    extract_map_run_id,
    get_map_run_base_path,
    get_map_run_manifest_path,
)


@pytest.mark.parametrize(
    "map_run_arn, expected_result",
    [
        pytest.param(
            "arn:aws:states:us-east-1:123456789012:mapRun:state-machine-name/execution-id:map-run-id",
            "map-run-id",
            id="Standard ARN format",
        ),
        pytest.param(
            "arn:aws:states:eu-west-1:123456789012:mapRun:complex-state-machine-name-with-hyphens/long-execution-id-12345:map-run-id-abc123",
            "map-run-id-abc123",
            id="Complex ARN with hyphens",
        ),
        pytest.param(
            "arn:aws:states:ap-south-1:123456789012:mapRun:state_machine_name/execution_id:map_run_id_123",
            "map_run_id_123",
            id="ARN with underscores",
        ),
        pytest.param(
            "arn:aws:states:us-west-2:123456789012:mapRun:sm/exec-id:run-id",
            "run-id",
            id="ARN with short names",
        ),
    ],
)
def test_extract_map_run_id_valid(map_run_arn: str, expected_result: str):
    """Test extracting map run ID from valid ARNs"""
    result = extract_map_run_id(map_run_arn)
    assert result == expected_result


@pytest.mark.parametrize(
    "map_run_arn",
    [
        pytest.param(
            "arn:aws:states:us-east-1:123456789012:mapRun:state-machine-name",
            id="ARN without execution and run IDs",
        ),
        pytest.param(
            "arn:aws:states:us-east-1:123456789012:mapRun:state-machine-name/execution-id",
            id="ARN without run ID",
        ),
        pytest.param(
            "invalid-arn-format",
            id="Completely invalid ARN",
        ),
        pytest.param(
            "",
            id="Empty string",
        ),
    ],
)
def test_extract_map_run_id_invalid(map_run_arn: str):
    """Test extracting map run ID from invalid ARNs raises ValueError"""
    with pytest.raises(ValueError):
        extract_map_run_id(map_run_arn)


@pytest.mark.parametrize(
    "map_run_arn, map_run_prefix, expected_result",
    [
        pytest.param(
            "arn:aws:states:us-east-1:123456789012:mapRun:state-machine-name/execution-id:map-run-id",
            "my-bucket/prefix",
            "my-bucket/prefix/map-run-id/",
            id="Standard prefix",
        ),
        pytest.param(
            "arn:aws:states:us-east-1:123456789012:mapRun:state-machine-name/execution-id:map-run-id",
            "my-bucket/nested/folders",
            "my-bucket/nested/folders/map-run-id/",
            id="Nested prefix",
        ),
        pytest.param(
            "arn:aws:states:us-east-1:123456789012:mapRun:state-machine-name/execution-id:map-run-id",
            "my-bucket/prefix/",
            "my-bucket/prefix/map-run-id/",
            id="Prefix with trailing slash",
        ),
    ],
)
def test_get_map_run_base_path(
    map_run_arn: str, map_run_prefix: str, expected_result: str
):
    """Test generating base S3 path for map run"""
    result = get_map_run_base_path(map_run_arn, map_run_prefix)
    assert result == expected_result


@pytest.mark.parametrize(
    "map_run_arn, map_run_prefix, expected_result",
    [
        pytest.param(
            "arn:aws:states:us-east-1:123456789012:mapRun:state-machine-name/execution-id:map-run-id",
            "my-bucket/prefix",
            "my-bucket/prefix/map-run-id/manifest.json",
            id="Standard prefix",
        ),
        pytest.param(
            "arn:aws:states:us-east-1:123456789012:mapRun:state-machine-name/execution-id:map-run-id",
            "my-bucket/nested/folders",
            "my-bucket/nested/folders/map-run-id/manifest.json",
            id="Nested prefix",
        ),
    ],
)
def test_get_map_run_manifest_path(
    map_run_arn: str, map_run_prefix: str, expected_result: str
):
    """Test generating manifest path for map run"""
    result = get_map_run_manifest_path(map_run_arn, map_run_prefix)
    assert result == expected_result
