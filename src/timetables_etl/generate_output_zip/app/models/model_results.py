"""
Models for State Machine Results files

- SUCCEEDED_n.json
- FAILED_n.json
Note: There is a PENDING_0.json unimplemented
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum, StrEnum
from typing import Annotated, Literal

import pydantic_core
from pydantic import BaseModel, Field, RootModel, ValidationError, WrapValidator
from structlog.stdlib import get_logger

log = get_logger()


def default_on_json_error(v, handler):
    """Handle JSON parsing errors by returning None and warning"""
    try:
        return handler(v)
    except Exception as e:
        log.warn(f"Failed to parse JSON field: {str(e)}")
        raise pydantic_core.PydanticUseDefault()


class ParsedInputData(BaseModel):
    """
    Parsed Input object
    The Input field is a string of json with the Map instance input for the task
    To get the Bucket/Key of the file we need to parse it as JSON in to a Pydantic model
    """

    Bucket: str | None = None
    DatasetRevisionId: str | None = None
    Key: str | None = None


class MapRunExecutionStatus(StrEnum):
    """Status values for map run executions"""

    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    ABORTED = "ABORTED"
    PENDING_REDRIVE = "PENDING_REDRIVE"


class MapExecutionBase(BaseModel):
    """Base model for execution results with common fields"""

    ExecutionArn: str = Field(pattern=r"^arn:aws:states:.*")
    Input: str

    InputDetails: dict[str, bool]
    Name: str = Field(min_length=1)
    OutputDetails: dict[str, bool]
    RedriveCount: int = Field(ge=0)
    RedriveStatus: Literal["REDRIVABLE", "NOT_REDRIVABLE", "REDRIVABLE_BY_MAP_RUN"]
    StartDate: datetime
    StateMachineArn: str = Field(pattern=r"^arn:aws:states:.*")
    StopDate: datetime
    # Custom Fields
    parsed_input: Annotated[
        ParsedInputData | None, WrapValidator(default_on_json_error)
    ] = None

    def model_post_init(self, __context) -> None:
        """Parse Input JSON after initialization"""
        try:
            self.parsed_input = ParsedInputData.model_validate_json(
                self.Input,
                strict=False,
                context={"log_errors": True},
            )
        except ValidationError:
            log.warn(
                "Failed to Validate Input JSON for a Task Result",
                execution_arn=self.ExecutionArn,
                exc_info=True,
            )


class MapExecutionSucceeded(MapExecutionBase):
    """Model for successful execution results"""

    Status: Literal[MapRunExecutionStatus.SUCCEEDED]
    Output: str
    RedriveStatusReason: str = Field(min_length=1)


class MapExecutionFailed(MapExecutionBase):
    """Model for failed execution results"""

    Status: Literal[MapRunExecutionStatus.FAILED]
    Cause: str = Field(min_length=1)
    Error: str = Field(min_length=1)


class MapResultSucceeded(RootModel[list[MapExecutionSucceeded]]):
    """Root model for SUCCEEDED_n.json files"""


class MapResultFailed(RootModel[list[MapExecutionFailed]]):
    """Root model for FAILED_n.json files"""


@dataclass
class MapResults:
    """Container for map execution results"""

    succeeded: list[MapExecutionSucceeded]
    failed: list[MapExecutionFailed]


class ResultType(str, Enum):
    """Valid result types for Step Functions Map state"""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    PENDING = "PENDING"
