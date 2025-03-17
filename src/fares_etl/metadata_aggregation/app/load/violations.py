"""
Load fares metadata into database
"""

from common_layer.database.client import SqlDB
from common_layer.database.models.model_fares import (
    FaresValidation,
    FaresValidationResult,
)
from common_layer.database.repos.repo_fares import (
    FaresValidationRepo,
    FaresValidationResultRepo,
)


def load_violations(
    db: SqlDB,
    violations: list[FaresValidation],
    fares_validation_result: FaresValidationResult,
) -> None:
    """
    Load metadata
    """
    fares_validation_repo = FaresValidationRepo(db)
    fares_validation_result_repo = FaresValidationResultRepo(db)

    fares_validation_repo.bulk_insert(violations)
    fares_validation_result_repo.insert(fares_validation_result)
