"""
Executions
"""

from datetime import datetime, timedelta
from functools import cached_property
from typing import Annotated

from pydantic import BaseModel, Field, computed_field

from ..helpers import calculate_duration


class InputDetails(BaseModel):
    """Details about the input data for a Step Functions execution."""

    included: bool = Field(
        description="Indicates whether the input is included in the response."
    )


class OutputDetails(BaseModel):
    """Details about the output data for a Step Functions execution."""

    included: bool = Field(
        description="Indicates whether the output is included in the response."
    )


class HTTPHeadersModel(BaseModel):
    """HTTP headers from the AWS Step Functions API response."""

    x_amzn_requestid: Annotated[
        str,
        Field(alias="x-amzn-requestid", description="AWS request ID for the API call."),
    ]
    date: str = Field(description="Timestamp when the response was sent.")
    content_type: Annotated[
        str,
        Field(alias="content-type", description="MIME type of the response content."),
    ]
    content_length: Annotated[
        str,
        Field(
            alias="content-length",
            description="Length of the response content in bytes.",
        ),
    ]
    connection: str = Field(description="Connection status for the HTTP request.")


class ResponseMetadataModel(BaseModel):
    """Metadata about the AWS API response."""

    RequestId: str = Field(description="AWS request ID for tracking the API call.")
    HTTPStatusCode: int = Field(description="HTTP status code of the response.")
    HTTPHeaders: HTTPHeadersModel = Field(
        description="HTTP headers included in the response."
    )
    RetryAttempts: int = Field(
        description="Number of retry attempts made for the request."
    )


class DescribeExecutionResponse(BaseModel):
    """Response model for AWS Step Functions DescribeExecution API."""

    executionArn: str = Field(description="ARN of the execution.")
    stateMachineArn: str = Field(
        description="ARN of the state machine that was executed."
    )
    name: str = Field(description="Name of the execution.")
    status: str = Field(
        description="Current status of the execution (e.g., RUNNING, SUCCEEDED, FAILED)."
    )
    startDate: datetime = Field(description="Timestamp when the execution started.")
    stopDate: datetime = Field(description="Timestamp when the execution stopped.")
    input: str = Field(
        description="String that contains the input data for the execution."
    )
    inputDetails: InputDetails = Field(description="Details about the execution input.")
    output: str = Field(description="Output data from the execution.")
    outputDetails: OutputDetails = Field(
        description="Details about the execution output."
    )
    traceHeader: str = Field(description="AWS X-Ray trace header for the execution.")
    redriveCount: int = Field(
        description="Number of times the execution has been redriven."
    )
    redriveStatus: str = Field(description="Current redrive status of the execution.")
    redriveStatusReason: str = Field(
        description="Reason for the current redrive status."
    )
    ResponseMetadata: ResponseMetadataModel = Field(
        description="Metadata about the API response."
    )

    @computed_field
    @cached_property
    def duration(self) -> timedelta:
        """Calculates the duration of the execution."""
        return calculate_duration(self.startDate, self.stopDate)
