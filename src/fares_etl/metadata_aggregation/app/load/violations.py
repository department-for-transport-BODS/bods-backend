"""
Load fares metadata into database
"""

from common_layer.database.client import SqlDB
from common_layer.database.models import FaresValidation, FaresValidationResult
from common_layer.database.repos import FaresValidationRepo, FaresValidationResultRepo


def load_violations(
    db: SqlDB,
    violations: list[FaresValidation],
    fares_validation_result: FaresValidationResult,
) -> None:
    """
    Load Fares Validation Results

    Tables:
        - fares_validator_faresvalidation
        - fares_validator_faresvalidationresult
    """
    fares_validation_repo = FaresValidationRepo(db)
    fares_validation_result_repo = FaresValidationResultRepo(db)

    fares_validation_repo.bulk_insert(violations)
    fares_validation_result_repo.insert(fares_validation_result)
