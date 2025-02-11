"""
Post Schema TXC Validation
"""

from typing import Callable, List

from common_layer.database.client import SqlDB
from common_layer.xml.txc.models import TXCData
from structlog.stdlib import get_logger

from .models import ValidationResult
from .validators import check_filename_for_filepath_pii, check_service_code_exists

log = get_logger()

ValidatorFn = Callable[[TXCData, SqlDB], List[ValidationResult]]


POST_SCHEMA_VALIDATORS: list[ValidatorFn] = [
    check_filename_for_filepath_pii,
    check_service_code_exists,
]


def run_post_schema_validations(txc_data: TXCData, db: SqlDB) -> list[ValidationResult]:
    """
    Run all validators and return their results
    """
    results: list[ValidationResult] = []

    for validator in POST_SCHEMA_VALIDATORS:
        validation_results = validator(txc_data, db)
        for result in validation_results:
            if not result.is_valid:
                log.info(
                    "Validation failed",
                    validator=validator.__name__,
                    error_code=result.error_code,
                    message=result.message,
                )
            results.append(result)

    return results
