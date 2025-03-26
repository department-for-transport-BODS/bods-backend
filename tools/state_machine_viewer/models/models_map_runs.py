"""
Maps Runs
"""

from datetime import datetime, timedelta
from functools import cached_property
from typing import Literal

from pydantic import BaseModel, computed_field

from tools.state_machine_viewer.helpers import calculate_duration


class ItemCounts(BaseModel):
    """
    Counts of items processed in child workflow executions, categorized by status.
    """

    pending: int
    running: int
    succeeded: int
    failed: int
    timedOut: int
    aborted: int
    total: int
    resultsWritten: int
    failuresNotRedrivable: int
    pendingRedrive: int


class ExecutionCounts(BaseModel):
    """
    Counts of child workflow executions, categorized by status.
    """

    pending: int
    running: int
    succeeded: int
    failed: int
    timedOut: int
    aborted: int
    total: int
    resultsWritten: int
    failuresNotRedrivable: int
    pendingRedrive: int


class MapRunDescribe(BaseModel):
    """
    Detailed information about a Map Run.
    """

    mapRunArn: str
    executionArn: str
    status: Literal["RUNNING", "SUCCEEDED", "FAILED", "ABORTED"]
    startDate: datetime
    stopDate: datetime | None = None
    maxConcurrency: int
    toleratedFailurePercentage: float | None = None
    toleratedFailureCount: int | None = None
    itemCounts: ItemCounts
    executionCounts: ExecutionCounts
    redriveCount: int
    redriveDate: datetime | None = None

    @computed_field
    @cached_property
    def duration(self) -> timedelta:
        """Calculates the duration of the Map Run execution."""
        end_time = self.stopDate if self.stopDate else datetime.now()
        return end_time - self.startDate


class MapRunListItem(BaseModel):
    """
    Map Run List
    """

    executionArn: str
    mapRunArn: str
    stateMachineArn: str
    startDate: datetime
    stopDate: datetime

    @computed_field
    @cached_property
    def duration(self) -> timedelta:
        """Calculates the duration of the execution."""
        return calculate_duration(self.startDate, self.stopDate)


class MapRunInfo(BaseModel):
    """
    Grouped Info
    """

    listing: MapRunListItem
    describe: MapRunDescribe
