"""
Common Exception logic
"""

import inspect
from typing import Any, TypedDict


class ETLErrorDict(TypedDict):
    """
    ETL Error Dict
    """

    ErrorCode: str
    Cause: str
    Context: dict[str, str | int]


class ETLException(Exception):
    """
    Base exception for errors in the ETL process.
    These Exceptions are not program crashes but instead issues with the input data
    """

    code = "SYSTEM_ERROR"
    message_template = "An error occurred in the ETL process."
    filename_template = "File: {filename}, Line: {line}"

    def __init__(
        self,
        message: Any | None = None,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        It accepts arbitrary keys like structlog's logger
        Try to get caller information, but fall back gracefully if it fails
            - caller information
            - Additional Context
            - All the base Exception Class init


        """
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
            self.message = self.message_template
        else:
            self.message = message if isinstance(message, str) else str(message)

        super().__init__(self.message)

    def __str__(self) -> str:
        """Format the exception as a human-readable string."""
        return (
            f"[{self.code}] {self.message} "
            f"({self.filename_template.format(filename=self.filename, line=self.line)})"
        )

    def to_dict(self) -> ETLErrorDict:
        """Convert the exception details to a dictionary for Step Functions."""
        context_dict: dict[str, Any] = {"File": self.filename, "Line": self.line}

        context_dict.update(self.context)

        return {
            "ErrorCode": self.code,
            "Cause": self.message,
            "Context": context_dict,
        }
