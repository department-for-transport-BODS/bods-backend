from datetime import datetime
from typing import Any
from unittest import mock

import pytest
from common_layer.database.models import FaresValidation, FaresValidationResult

from fares_etl.metadata_aggregation.app.transform.transform_violations import (
    map_violations,
)


@pytest.mark.parametrize(
    "violations,expected_fares_validations,expected_fares_validation_result",
    [
        pytest.param(
            [
                {
                    "FileName": {"S": "file_name.xml"},
                    "Violations": {
                        "L": [
                            {
                                "M": {
                                    "category": {"S": "Eligibility"},
                                    "line": {"N": "1472"},
                                    "observation": {"S": "Test observation"},
                                }
                            }
                        ]
                    },
                }
            ],
            [
                FaresValidation(
                    file_name="file_name.xml",
                    category="Eligibility",
                    error_line_no=1472,
                    error="Test observation",
                    organisation_id=1,
                    revision_id=1,
                )
            ],
            FaresValidationResult(
                organisation_id=1,
                revision_id=1,
                count=1,
                report_file_name="BODS_Fares_Validation_1_1_00_00_01012025.xlsx",
            ),
        ),
        pytest.param(
            [
                {
                    "FileName": {"S": "file_name.xml"},
                    "Violations": {
                        "L": [
                            {
                                "M": {
                                    "category": {"S": "Eligibility"},
                                    "line": {"N": "1472"},
                                    "observation": {"S": "Test observation"},
                                }
                            },
                            {
                                "M": {
                                    "category": {"S": "Compliance"},
                                    "line": {"N": "516"},
                                    "observation": {"S": "Test observation 2"},
                                }
                            },
                        ]
                    },
                }
            ],
            [
                FaresValidation(
                    file_name="file_name.xml",
                    category="Eligibility",
                    error_line_no=1472,
                    error="Test observation",
                    organisation_id=1,
                    revision_id=1,
                ),
                FaresValidation(
                    file_name="file_name.xml",
                    category="Compliance",
                    error_line_no=516,
                    error="Test observation 2",
                    organisation_id=1,
                    revision_id=1,
                ),
            ],
            FaresValidationResult(
                organisation_id=1,
                revision_id=1,
                count=2,
                report_file_name="BODS_Fares_Validation_1_1_00_00_01012025.xlsx",
            ),
        ),
        pytest.param(
            [],
            [],
            FaresValidationResult(
                organisation_id=1,
                revision_id=1,
                count=0,
                report_file_name="BODS_Fares_Validation_1_1_00_00_01012025.xlsx",
            ),
        ),
    ],
)
def test_map_violations(
    violations: list[dict[str, Any]],
    expected_fares_validations: list[FaresValidation],
    expected_fares_validation_result: FaresValidationResult,
):
    with mock.patch(
        "fares_etl.metadata_aggregation.app.transform.transform_violations.datetime"
    ) as mock_datetime:
        mock_datetime.now.return_value = datetime(2025, 1, 1, 0, 0, 0)
        fares_validations, fares_validation_result = map_violations(violations, 1, 1)

        assert fares_validations == expected_fares_validations
        assert fares_validation_result.count == expected_fares_validation_result.count
        assert (
            fares_validation_result.report_file_name
            == expected_fares_validation_result.report_file_name
        )
