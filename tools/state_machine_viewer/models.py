"""
State Machine Viewer Models
"""

from datetime import datetime, timedelta
from typing import Annotated

from pydantic import BaseModel, Field


class StepDuration(BaseModel):
    """Step execution duration information."""

    name: str
    duration: timedelta
    start_time: datetime
    end_time: datetime


class MapItemDuration(BaseModel):
    """Duration information for map state items."""

    index: int
    duration: timedelta
    step_name: str


class CloudWatchEventsExecutionDataDetails(BaseModel):
    """CloudWatch Events execution data details."""

    included: bool = False
    truncated: bool = False


class ExecutionDetails(BaseModel):
    """AWS Step Function execution details."""

    execution_arn: str
    state_machine_arn: str
    name: str
    status: str
    start_time: datetime
    end_time: datetime | None = None
    duration: Annotated[timedelta, Field(default_factory=timedelta)]
    steps: Annotated[list[StepDuration], Field(default_factory=list)] = []
    map_items: Annotated[list[MapItemDuration], Field(default_factory=list)] = []

    # Added fields
    input: str = ""
    input_details: Annotated[
        CloudWatchEventsExecutionDataDetails,
        Field(default_factory=CloudWatchEventsExecutionDataDetails),
    ]
    output: str = ""
    output_details: Annotated[
        CloudWatchEventsExecutionDataDetails,
        Field(default_factory=CloudWatchEventsExecutionDataDetails),
    ]
    map_run_arn: str = ""
    error: str = ""
    cause: str = ""
