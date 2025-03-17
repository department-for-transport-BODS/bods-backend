"""
Exception Handler Pydantic models and Dataclasses
"""

import json
from typing import Annotated

from common_layer.database.models import ETLErrorCode
from pydantic import BaseModel, ConfigDict, Field


class ErrorCause(BaseModel):
    """
    Structured error details from parsed Cause.
    """

    model_config = ConfigDict(populate_by_name=True)

    error_message: str = Field(alias="errorMessage")  # This contains the JSON string
    error_type: str = Field(alias="errorType")
    request_id: str = Field(alias="requestId")
    stack_trace: Annotated[list[str] | None, Field(alias="stackTrace", default=None)]

    @property
    def extracted_error(self) -> dict | None:
        """Extracts and parses the original error JSON from error_message."""
        try:
            return json.loads(self.error_message)  # Parse the JSON string
        except (json.JSONDecodeError, AttributeError):
            return None

    @property
    def error_code(self) -> ETLErrorCode:
        """Extracts and converts the original error code from the parsed errorMessage."""
        parsed = self.extracted_error
        if parsed and "ErrorCode" in parsed:
            return (
                ETLErrorCode[parsed["ErrorCode"]]
                if parsed["ErrorCode"] in ETLErrorCode.__members__
                else ETLErrorCode.SYSTEM_ERROR
            )
        return ETLErrorCode.SYSTEM_ERROR

    @property
    def extracted_message(self) -> str:
        """Extracts the original error message from the parsed errorMessage."""
        parsed = self.extracted_error
        return parsed["Cause"] if parsed and "Cause" in parsed else self.error_message


class ExceptionHandlerInputData(BaseModel):
    """
    Exception Handler Input Event with JSONata structured error handling
    """

    model_config = ConfigDict(populate_by_name=True)

    error: str = Field(alias="Error")
    cause: Annotated[ErrorCause, Field(alias="Cause")]
    dataset_etl_task_result_id: int = Field(alias="DatasetEtlTaskResultId")
