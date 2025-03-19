"""
Common Exception logic
"""

import inspect
import json
from typing import Any, TypedDict

from common_layer.database.models import ETLErrorCode


class ETLErrorDict(TypedDict):
    """
    ETL Error Dict
    """

    ErrorCode: ETLErrorCode
    Cause: str
    Context: dict[str, str | int]


class ETLException(Exception):
    """
    Base exception for errors in the ETL process.
    These Exceptions are not program crashes but instead issues with the input data
    """

    code: ETLErrorCode = ETLErrorCode.SYSTEM_ERROR
    filename_template = "File: {filename}, Line: {line}"

    def __init__(
        self,
        message: Any | None = None,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        try:
            frame_info = inspect.stack()[1]
            self.filename = frame_info.filename
            self.line = frame_info.lineno
        except (IndexError, AttributeError):
            self.filename = "<unknown>"
            self.line = 0

        self.context = context or {}
        self.context.update(kwargs)

        if message is None:
            self.message = self.code.value
        else:
            self.message = message if isinstance(message, str) else str(message)

        super().__init__(self.message)

    def __str__(self) -> str:
        """Format the exception as a JSON string matching the to_dict() structure."""
        return json.dumps(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        """Convert the exception details to a dictionary for Step Functions."""
        context_dict: dict[str, Any] = {"File": self.filename, "Line": self.line}

        context_dict.update(self.context)

        return {
            "ErrorCode": self.code.name,
            "Cause": self.message,
            "Context": context_dict,
        }
