"""
Post Schema TXC Validation
"""

from typing import Callable

from common_layer.txc.models.txc_data import TXCData
from structlog.stdlib import get_logger

from .models import ValidationResult
from .validators import check_filename_for_filepath_pii

log = get_logger()

ValidatorFn = Callable[[TXCData], ValidationResult]


POST_SCHEMA_VALIDATORS: list[ValidatorFn] = [
    check_filename_for_filepath_pii,
]


def run_post_schema_validations(txc_data: TXCData) -> list[ValidationResult]:
    """
    Run all validators and return their results
    """
    results: list[ValidationResult] = []

    for validator in POST_SCHEMA_VALIDATORS:
        result = validator(txc_data)
        if not result.is_valid:
            log.info(
                "Validation failed",
                validator=validator.__name__,
                error_code=result.error_code,
                message=result.message,
            )
        results.append(result)

    return results
