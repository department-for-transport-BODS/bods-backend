"""
Exception Handler Pydantic models and Dataclasses
"""

from typing import Annotated

from common_layer.database.models.model_pipelines import ETLErrorCode
from pydantic import BaseModel, ConfigDict, Field


class ErrorCause(BaseModel):
    """
    Structured error details from parsed Cause
    """

    model_config = ConfigDict(populate_by_name=True)

    error_message: str = Field(alias="errorMessage")
    error_type: str = Field(alias="errorType")
    request_id: str = Field(alias="requestId")
    stack_trace: Annotated[list[str] | None, Field(alias="stackTrace", default=None)]


class ExceptionHandlerInputData(BaseModel):
    """
    Exception Handler Input Event with JSONata structured error handling
    """

    model_config = ConfigDict(populate_by_name=True)

    error: str = Field(alias="Error")
    cause: Annotated[ErrorCause, Field(alias="Cause")]
    dataset_etl_task_result_id: int = Field(alias="DatasetEtlTaskResultId")

    @property
    def error_code(self) -> ETLErrorCode:
        """Converts the error string into an ETLErrorCode enum."""
        return (
            ETLErrorCode[self.error]
            if self.error in ETLErrorCode.__members__
            else ETLErrorCode.SYSTEM_ERROR
        )
