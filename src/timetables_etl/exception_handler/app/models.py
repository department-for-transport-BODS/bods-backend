"""
Exception Handler Pydantic models and Dataclasses
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetails(BaseModel):
    """
    Structured error details from parsed Cause
    """

    error_message: str = Field(alias="ErrorMessage")
    error_type: str = Field(alias="ErrorType")
    request_id: str = Field(alias="RequestId")
    stack_trace: list[str] = Field(alias="StackTrace")


class ExceptionHandlerInputData(BaseModel):
    """
    Exception Handler Input Event with JSONata structured error handling
    """

    model_config = ConfigDict(populate_by_name=True)

    error: str = Field(alias="Error")
    error_details: Annotated[ErrorDetails, Field(alias="ErrorDetails")]
    dataset_etl_task_result_id: int = Field(alias="DatasetEtlTaskResultId")
    execution_context: dict = Field(alias="ExecutionContext")
