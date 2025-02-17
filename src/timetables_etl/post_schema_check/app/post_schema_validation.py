"""
Post Schema TXC Validation
"""

import os
from typing import Callable

from common_layer.database.client import SqlDB
from common_layer.xml.txc.models import TXCData
from structlog.stdlib import get_logger

from .models import ValidationResult
from .validators import check_filename_for_filepath_pii, check_service_code_exists

log = get_logger()

ValidatorFn = Callable[[TXCData, SqlDB], list[ValidationResult]]


def is_service_check_enabled() -> bool:
    """
    Return if service check is enabled
    """
    return os.environ.get("SERVICE_CHECK_ENABLED", "false").lower() == "true"


def get_active_validators() -> list[ValidatorFn]:
    """
    Returns a list of validator functions to run
    """
    validators = [check_filename_for_filepath_pii]

    if is_service_check_enabled():
        validators.append(check_service_code_exists)

    return validators


def run_post_schema_validations(txc_data: TXCData, db: SqlDB) -> list[ValidationResult]:
    """
    Run all validators and return their results
    """
    results: list[ValidationResult] = []

    for validator in get_active_validators():
        validation_results = validator(txc_data, db)
        for result in validation_results:
            if not result.is_valid:
                log.info(
                    "Validation failed",
                    validator=validator.__name__,
                    error_code=result.error_code,
                    additional_details=result.additional_details,
                    message=result.message,
                )
            results.append(result)

    return results
