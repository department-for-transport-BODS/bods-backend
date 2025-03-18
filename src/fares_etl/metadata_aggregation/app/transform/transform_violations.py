"""
Transform fares metadata items
"""

from datetime import datetime, timezone
from typing import Any

from boto3.dynamodb.types import TypeDeserializer
from common_layer.database.models import FaresValidation, FaresValidationResult


def map_violations(
    violation_items: list[dict[str, Any]], organisation_id: int, revision_id: int
) -> tuple[list[FaresValidation], FaresValidationResult]:
    """
    Map dynamo response to FaresViolation
    """
    fares_violations_list: list[FaresValidation] = []
    type_deserializer = TypeDeserializer()

    for item in violation_items:
        file_name = type_deserializer.deserialize(item["FileName"])
        violations = type_deserializer.deserialize(item["Violations"])

        for violation in violations:
            fares_violations_list.append(
                FaresValidation(
                    file_name=file_name,
                    category=violation["category"],
                    error_line_no=violation["line"],
                    error=violation["observation"],
                    organisation_id=organisation_id,
                    revision_id=revision_id,
                )
            )

    current_time = datetime.now(timezone.utc).strftime("%H_%M_%d%m%Y")

    fares_validator_report_name = (
        f"BODS_Fares_Validation_{organisation_id}_{revision_id}_{current_time}.xlsx"
    )

    fares_validation_result = FaresValidationResult(
        organisation_id=organisation_id,
        revision_id=revision_id,
        count=len(fares_violations_list),
        report_file_name=fares_validator_report_name,
    )

    return fares_violations_list, fares_validation_result
