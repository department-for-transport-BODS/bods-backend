"""
TXC PTI Step Exceptions
"""

from common_layer.database.models import ETLErrorCode

from .exceptions_common import ETLException


class PTIViolationFound(ETLException):
    """1 or more PTI Validation Violations Found"""

    code = ETLErrorCode.PTI_VIOLATION_FOUND
