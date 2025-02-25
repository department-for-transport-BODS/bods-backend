"""
ResourceFrame Helpers
"""

from structlog.stdlib import get_logger

from ..models import ResourceFrame

log = get_logger()


def get_national_operator_codes(frames: list[ResourceFrame]) -> list[str]:
    """
    Get List of National Operator Codes
    """
    operator_codes: set[str] = set()

    for frame in frames:
        for operator in frame.organisations:
            public_code = operator.PublicCode

            if public_code is not None:
                operator_codes.add(public_code)
            else:
                log.info("Operator Missing PublicCode", operator_id=operator.id)

    return list(operator_codes)
