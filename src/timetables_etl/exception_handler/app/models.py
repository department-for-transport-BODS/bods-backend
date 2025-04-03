"""
Exception Handler Pydantic models and Dataclasses
"""

import json
from typing import Annotated, Any

from common_layer.database.models import ETLErrorCode
from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    def extracted_error(self) -> dict[str, Any] | None:
        """Extracts and parses the original error JSON from error_message."""
        try:
            return json.loads(self.error_message)
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
    step_name: str = Field(alias="StepName", default="unknown")

    dataset_etl_task_result_id: int = Field(alias="DatasetEtlTaskResultId")

    fail_dataset_revision: bool | None = Field(
        alias="FailDatasetRevision", default=True
    )
    fail_dataset_etl_task_result: bool | None = Field(
        alias="FailDatasetETLTaskResult", default=True
    )

    @model_validator(mode="before")
    @classmethod
    def sanitize_event(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Handle inputs that don't match the expected ExceptionHandlerInputData model.
        For example, unexpected platform errors.
        """
        raw_cause: dict[str, Any] = values.get("Cause", {})

        if isinstance(raw_cause, str):
            try:
                raw_cause = json.loads(raw_cause)
            except json.JSONDecodeError:
                raw_cause = {"errorMessage": raw_cause}

        raw_cause.setdefault("errorType", "unknown")
        raw_cause.setdefault("errorMessage", "unknown")
        raw_cause.setdefault("requestId", "unknown")
        raw_cause.setdefault("stackTrace", [])

        values["Cause"] = raw_cause

        return values
