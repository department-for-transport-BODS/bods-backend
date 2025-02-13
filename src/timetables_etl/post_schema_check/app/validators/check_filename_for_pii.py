"""
Check Filename for PII
"""

import re

from common_layer.database.client import SqlDB
from common_layer.xml.txc.models import TXCData
from structlog.stdlib import get_logger

from ..models import ValidationResult

log = get_logger()


def check_filename_for_filepath_pii(
    txc_data: TXCData, _db: SqlDB
) -> list[ValidationResult]:
    """
    Check if a TransXChange document's filename contains potential PII through filepath information.

    Examines the FileName attribute of a TransXChange document for path separators:
    - Backslashes which indicate Windows-style file paths
    - Forward slashes which indicate Unix (Mac / Linux) file paths
    Both may contain usernames or sensitive path information
    """
    if txc_data.Metadata is None:
        return [ValidationResult(is_valid=True)]

    windows_paths = re.findall("\\\\", txc_data.Metadata.FileName)
    unix_paths = re.findall("/", txc_data.Metadata.FileName)

    if len(windows_paths) > 0 or len(unix_paths) > 0:
        log.warning("Found potential file path in TransXChange FileName Attribute")
        return [
            ValidationResult(
                is_valid=False,
                error_code="PII ERROR",
                message="Filename contains potential filepath PII",
            )
        ]
    return [ValidationResult(is_valid=True)]
