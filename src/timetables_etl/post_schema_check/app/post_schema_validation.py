"""
Post Schema TXC Validation
"""

from typing import Callable

from common_layer.database.client import SqlDB
from common_layer.txc.models.txc_data import TXCData
from structlog.stdlib import get_logger

from .models import ValidationResult
from .validators import check_filename_for_filepath_pii, check_service_code_exists

log = get_logger()

SimpleValidatorFn = Callable[[TXCData], ValidationResult]
DBValidatorFn = Callable[[TXCData, SqlDB], ValidationResult]


SIMPLE_POST_SCHEMA_VALIDATORS: list[SimpleValidatorFn] = [
    check_filename_for_filepath_pii,
]

DB_POST_SCHEMA_VALIDATORS: list[DBValidatorFn] = [
    check_service_code_exists,
]


def run_post_schema_validations(txc_data: TXCData, db: SqlDB) -> list[ValidationResult]:
    """
    Run all validators and return their results
    """
    results: list[ValidationResult] = []

    for validator in SIMPLE_POST_SCHEMA_VALIDATORS:
        result = validator(txc_data)
        if not result.is_valid:
            log.info(
                "Validation failed",
                validator=validator.__name__,
                error_code=result.error_code,
                message=result.message,
            )
        results.append(result)

    for validator in DB_POST_SCHEMA_VALIDATORS:
        results = validator(txc_data, db)
        for result in results:
            if not result.is_valid:
                log.info(
                    "Validation failed",
                    validator=validator.__name__,
                    error_code=result.error_code,
                    message=result.message,
                )
            results.append(result)

    return results
