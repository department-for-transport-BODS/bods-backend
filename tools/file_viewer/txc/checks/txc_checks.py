"""
TXC Checks
"""

from ...checks import Check, CheckInputData, CheckOutputData
from .duplicate_journeys import (
    check_duplicate_journeys,
    check_duplicate_journeys_details,
)

CHECKS: list[Check[CheckInputData, CheckOutputData]] = [  # type: ignore
    Check(
        "Duplicate journeys", check_duplicate_journeys, check_duplicate_journeys_details
    ),
]
