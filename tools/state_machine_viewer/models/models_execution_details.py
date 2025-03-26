"""
State Machine Viewer Models
"""

from datetime import datetime, timedelta

from pydantic import BaseModel

from .models_describe_executions import DescribeExecutionResponse
from .models_execution_history import HistoryEvent
from .models_map_runs import MapRunListItem


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


class ExecutionDetails(BaseModel):
    """AWS Step Function execution details."""

    describe: DescribeExecutionResponse
    history: list[HistoryEvent]
    map_runs: list[MapRunListItem]
