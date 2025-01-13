"""
Tests for parsing Manifest.json into Pydantic Models
"""

import pytest
from generate_output_zip.app.models import (
    ManifestResultFile,
    ManifestResultFilesStatus,
    MapResultManifest,
)
from pydantic import ValidationError


@pytest.mark.parametrize(
    "json_str,expected_model",
    [
        pytest.param(
            """
            {
                "DestinationBucket": "bodds-dev",
                "MapRunArn": "arn:aws:states:eu-west-2:228266753808:mapRun:bods-backend-dev-tt-sm/8c9dd6c6-f907-3584-9153-f8a2f1bfe7ce:25bc2fbb-6f60-4c44-876b-3cc9586fc435",
                "ResultFiles": {
                    "FAILED": [
                        {
                            "Key": "tt-etl-map-results/25bc2fbb-6f60-4c44-876b-3cc9586fc435/FAILED_0.json",
                            "Size": 80039
                        }
                    ],
                    "PENDING": [],
                    "SUCCEEDED": [
                        {
                            "Key": "tt-etl-map-results/25bc2fbb-6f60-4c44-876b-3cc9586fc435/SUCCEEDED_0.json",
                            "Size": 229628
                        }
                    ]
                }
            }
            """,
            MapResultManifest(
                DestinationBucket="bodds-dev",
                MapRunArn="arn:aws:states:eu-west-2:228266753808:mapRun:bods-backend-dev-tt-sm/8c9dd6c6-f907-3584-9153-f8a2f1bfe7ce:25bc2fbb-6f60-4c44-876b-3cc9586fc435",
                ResultFiles=ManifestResultFilesStatus(
                    FAILED=[
                        ManifestResultFile(
                            Key="tt-etl-map-results/25bc2fbb-6f60-4c44-876b-3cc9586fc435/FAILED_0.json",
                            Size=80039,
                        )
                    ],
                    PENDING=[],
                    SUCCEEDED=[
                        ManifestResultFile(
                            Key="tt-etl-map-results/25bc2fbb-6f60-4c44-876b-3cc9586fc435/SUCCEEDED_0.json",
                            Size=229628,
                        )
                    ],
                ),
            ),
            id="Standard Manifest With Mixed Results",
        ),
        pytest.param(
            """
            {
                "DestinationBucket": "bodds-prod",
                "MapRunArn": "arn:aws:states:eu-west-2:228266753808:mapRun:bods-backend-prod-tt-sm/abc123",
                "ResultFiles": {
                    "FAILED": [],
                    "PENDING": [],
                    "SUCCEEDED": [
                        {
                            "Key": "tt-etl-map-results/abc123/SUCCEEDED_0.json",
                            "Size": 1000
                        },
                        {
                            "Key": "tt-etl-map-results/abc123/SUCCEEDED_1.json",
                            "Size": 2000
                        }
                    ]
                }
            }
            """,
            MapResultManifest(
                DestinationBucket="bodds-prod",
                MapRunArn="arn:aws:states:eu-west-2:228266753808:mapRun:bods-backend-prod-tt-sm/abc123",
                ResultFiles=ManifestResultFilesStatus(
                    FAILED=[],
                    PENDING=[],
                    SUCCEEDED=[
                        ManifestResultFile(
                            Key="tt-etl-map-results/abc123/SUCCEEDED_0.json", Size=1000
                        ),
                        ManifestResultFile(
                            Key="tt-etl-map-results/abc123/SUCCEEDED_1.json", Size=2000
                        ),
                    ],
                ),
            ),
            id="All Succeeded Results Multiple Files",
        ),
        pytest.param(
            """
            {
                "DestinationBucket": "bodds-dev",
                "MapRunArn": "arn:aws:states:eu-west-2:228266753808:mapRun:bods-backend-dev-tt-sm/xyz789",
                "ResultFiles": {
                    "FAILED": [],
                    "PENDING": [
                        {
                            "Key": "tt-etl-map-results/xyz789/PENDING_0.json",
                            "Size": 500
                        }
                    ],
                    "SUCCEEDED": []
                }
            }
            """,
            MapResultManifest(
                DestinationBucket="bodds-dev",
                MapRunArn="arn:aws:states:eu-west-2:228266753808:mapRun:bods-backend-dev-tt-sm/xyz789",
                ResultFiles=ManifestResultFilesStatus(
                    FAILED=[],
                    PENDING=[
                        ManifestResultFile(
                            Key="tt-etl-map-results/xyz789/PENDING_0.json", Size=500
                        )
                    ],
                    SUCCEEDED=[],
                ),
            ),
            id="Only Pending Results",
        ),
    ],
)
def test_manifest_parsing_valid(
    json_str: str, expected_model: MapResultManifest
) -> None:
    """
    Test parsing valid manifest.json data
    """
    manifest = MapResultManifest.model_validate_json(json_str)
    assert manifest == expected_model


@pytest.mark.parametrize(
    "json_str,expected_error_message",
    [
        pytest.param(
            """
            {
                "DestinationBucket": "",
                "MapRunArn": "arn:aws:states:eu-west-2:228266753808:mapRun:test",
                "ResultFiles": {
                    "FAILED": [],
                    "PENDING": [],
                    "SUCCEEDED": []
                }
            }
            """,
            "String should have at least 1 character",
            id="Empty Destination Bucket",
        ),
        pytest.param(
            """
            {
                "DestinationBucket": "bodds-dev",
                "MapRunArn": "invalid-arn-format",
                "ResultFiles": {
                    "FAILED": [],
                    "PENDING": [],
                    "SUCCEEDED": []
                }
            }
            """,
            "String should match pattern '^arn:aws:states:.*'",
            id="Invalid ARN Format",
        ),
        pytest.param(
            """
            {
                "DestinationBucket": "bodds-dev",
                "MapRunArn": "arn:aws:states:eu-west-2:228266753808:mapRun:test",
                "ResultFiles": {
                    "FAILED": [
                        {
                            "Key": "tt-etl-map-results/test/FAILED_0.json",
                            "Size": -100
                        }
                    ],
                    "PENDING": [],
                    "SUCCEEDED": []
                }
            }
            """,
            "Input should be greater than 0",
            id="Negative File Size",
        ),
        pytest.param(
            """
            {
                "DestinationBucket": "bodds-dev",
                "MapRunArn": "arn:aws:states:eu-west-2:228266753808:mapRun:test",
                "ResultFiles": {
                    "FAILED": [
                        {
                            "Key": "",
                            "Size": 100
                        }
                    ],
                    "PENDING": [],
                    "SUCCEEDED": []
                }
            }
            """,
            "String should have at least 1 character",
            id="Empty File Key",
        ),
        pytest.param(
            """
            {
                "DestinationBucket": "bodds-dev",
                "MapRunArn": "arn:aws:states:eu-west-2:228266753808:mapRun:test",
                "ResultFiles": {
                    "FAILED": [
                        {
                            "Size": 100
                        }
                    ],
                    "PENDING": [],
                    "SUCCEEDED": []
                }
            }
            """,
            "Field required",
            id="Missing Required Key Field",
        ),
        pytest.param(
            """
            {
                "DestinationBucket": "bodds-dev",
                "MapRunArn": "arn:aws:states:eu-west-2:228266753808:mapRun:test",
                "ResultFiles": {
                    "FAILED": [
                        {
                            "Key": "test.json"
                        }
                    ],
                    "PENDING": [],
                    "SUCCEEDED": []
                }
            }
            """,
            "Field required",
            id="Missing Required Size Field",
        ),
        pytest.param(
            """
            {
                "DestinationBucket": "bodds-dev",
                "MapRunArn": "arn:aws:states:eu-west-2:228266753808:mapRun:test",
                "ResultFiles": {
                    "FAILED": [
                        {
                            "Key": "test.json",
                            "Size": "not_a_number"
                        }
                    ],
                    "PENDING": [],
                    "SUCCEEDED": []
                }
            }
            """,
            "Input should be a valid integer",
            id="Invalid Size Type",
        ),
        pytest.param(
            """
            {
                "DestinationBucket": "bodds-dev",
                "ResultFiles": {
                    "FAILED": [],
                    "PENDING": [],
                    "SUCCEEDED": []
                }
            }
            """,
            "Field required",
            id="Missing Required MapRunArn",
        ),
        pytest.param(
            """
            {
                "DestinationBucket": "bodds-dev",
                "MapRunArn": "arn:aws:states:eu-west-2:228266753808:mapRun:test"
            }
            """,
            "Field required",
            id="Missing Required ResultFiles",
        ),
        pytest.param(
            """
            {
                "DestinationBucket": "bodds-dev",
                "MapRunArn": "arn:aws:states:eu-west-2:228266753808:mapRun:test",
                "ResultFiles": {
                    "FAILED": null,
                    "PENDING": [],
                    "SUCCEEDED": []
                }
            }
            """,
            "Input should be a valid array",
            id="Null Array Instead Of Empty Array",
        ),
    ],
)
def test_manifest_parsing_invalid(json_str: str, expected_error_message: str) -> None:
    """Test that invalid manifest.json data raises appropriate validation errors"""
    with pytest.raises(ValidationError) as exc_info:
        MapResultManifest.model_validate_json(json_str)
    assert expected_error_message in str(exc_info.value)
