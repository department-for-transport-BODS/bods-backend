"""
Models for Parsing Map Results
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Callable, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    ValidationError,
    ValidationInfo,
    WrapValidator,
)
from pydantic_core import PydanticUseDefault
from structlog.stdlib import get_logger

log = get_logger()


class MapRunExecutionStatus(StrEnum):
    """Status values for map run executions"""

    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    ABORTED = "ABORTED"
    PENDING_REDRIVE = "PENDING_REDRIVE"


class MapInputData(BaseModel):
    """
    Parsed Input object
    The Input field is a string of json with the Map instance input for the task
    To get the Bucket/Key of the file we need to parse it as JSON in to a Pydantic model
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )

    Bucket: Annotated[str | None, Field(None, alias="mapS3Bucket")] = None
    Key: Annotated[str | None, Field(None, alias="mapS3Object")] = None
    DatasetRevisionId: Annotated[
        int | None, Field(None, alias="mapDatasetRevisionId")
    ] = None
    mapDatasetEtlTaskResultId: int | None = None


def default_on_json_error(v: str, handler: Callable[[str], MapInputData]):
    """Handle JSON parsing errors by returning None and warning"""
    try:
        return handler(v)
    except Exception as e:
        log.warn(f"Failed to parse JSON field: {str(e)}")
        raise PydanticUseDefault() from e


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
        MapInputData | None, WrapValidator(default_on_json_error)
    ] = None

    def model_post_init(self, __context: ValidationInfo) -> None:
        """Parse Input JSON after initialization"""
        try:
            self.parsed_input = MapInputData.model_validate_json(
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
    Cause: str | None = None
    Error: str | None = None


class MapResultSucceeded(RootModel[list[MapExecutionSucceeded]]):
    """Root model for SUCCEEDED_n.json files"""


class MapResultFailed(RootModel[list[MapExecutionFailed]]):
    """Root model for FAILED_n.json files"""


@dataclass
class MapResults:
    """Container for map execution results"""

    succeeded: list[MapExecutionSucceeded]
    failed: list[MapExecutionFailed]
