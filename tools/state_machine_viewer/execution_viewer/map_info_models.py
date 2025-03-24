"""
Map Info Models
"""

from datetime import datetime, timedelta
from typing import Annotated

from pydantic import BaseModel, Field, computed_field


class MapRunStats(BaseModel):
    """Statistics about a Map Run execution."""

    # Item statistics
    total_items: Annotated[int, Field(default=0)]
    pending_items: Annotated[int, Field(default=0)]
    running_items: Annotated[int, Field(default=0)]
    succeeded_items: Annotated[int, Field(default=0)]
    failed_items: Annotated[int, Field(default=0)]
    timed_out_items: Annotated[int, Field(default=0)]
    aborted_items: Annotated[int, Field(default=0)]
    results_written: Annotated[int, Field(default=0)]
    failures_not_redrivable: Annotated[int, Field(default=0)]
    pending_redrive: Annotated[int, Field(default=0)]

    # Duration statistics
    avg_duration: Annotated[timedelta, Field(default_factory=timedelta)]
    min_duration: Annotated[timedelta, Field(default_factory=timedelta)]
    max_duration: Annotated[timedelta, Field(default_factory=timedelta)]
    total_duration: Annotated[timedelta, Field(default_factory=timedelta)]

    @computed_field
    def completion_percentage(self) -> float:
        """Calculate the percentage of items that have completed processing."""
        if self.total_items == 0:
            return 0.0
        completed = (
            self.succeeded_items
            + self.failed_items
            + self.timed_out_items
            + self.aborted_items
        )
        return round((completed / self.total_items) * 100, 2)

    @computed_field
    def success_percentage(self) -> float:
        """Calculate the percentage of items that succeeded."""
        if self.total_items == 0:
            return 0.0
        return round((self.succeeded_items / self.total_items) * 100, 2)


class MapExecutionItem(BaseModel):
    """Details of an individual Map execution."""

    # Execution identification
    execution_arn: Annotated[str, Field()]
    execution_name: Annotated[str, Field()]
    index: Annotated[int, Field()]

    # Execution status
    status: Annotated[str, Field()]

    # Timing information
    start_time: Annotated[datetime, Field()]
    end_time: Annotated[datetime | None, Field(default=None)]
    duration: Annotated[timedelta, Field(default_factory=timedelta)]

    # Result information
    input: Annotated[str | None, Field(default=None)]
    output: Annotated[str | None, Field(default=None)]
    error: Annotated[str | None, Field(default=None)]
    cause: Annotated[str | None, Field(default=None)]

    # Redrive information
    redrive_count: Annotated[int, Field(default=0)]
    redrive_date: Annotated[datetime | None, Field(default=None)]


class MapExecution(BaseModel):
    """Complete Map execution details including all child executions."""

    # Map run identification
    map_run_arn: Annotated[str, Field()]
    execution_arn: Annotated[str, Field()]
    state_machine_arn: Annotated[str, Field()]
    state_name: Annotated[str, Field()]

    # Status
    status: Annotated[str, Field()]

    # Timing
    start_time: Annotated[datetime, Field()]
    end_time: Annotated[datetime | None, Field(default=None)]
    duration: Annotated[timedelta, Field(default_factory=timedelta)]

    # Configuration
    max_concurrency: Annotated[int, Field()]
    tolerated_failure_percentage: Annotated[float, Field()]
    tolerated_failure_count: Annotated[int, Field()]

    # Redrive information
    redrive_count: Annotated[int, Field(default=0)]
    redrive_date: Annotated[datetime | None, Field(default=None)]

    # Child executions
    executions: Annotated[list[MapExecutionItem], Field(default_factory=list)]

    # Statistics
    stats: Annotated[MapRunStats, Field()]

    # Update statistics based on child executions
    def update_stats_from_executions(self) -> None:
        """Update statistics based on child executions."""
        if not self.executions:
            return

        durations = [
            ex.duration for ex in self.executions if ex.duration.total_seconds() > 0
        ]

        self.stats.total_items = len(self.executions)
        self.stats.pending_items = sum(
            1 for ex in self.executions if ex.status == "PENDING"
        )
        self.stats.running_items = sum(
            1 for ex in self.executions if ex.status == "RUNNING"
        )
        self.stats.succeeded_items = sum(
            1 for ex in self.executions if ex.status == "SUCCEEDED"
        )
        self.stats.failed_items = sum(
            1 for ex in self.executions if ex.status == "FAILED"
        )
        self.stats.timed_out_items = sum(
            1 for ex in self.executions if ex.status == "TIMED_OUT"
        )
        self.stats.aborted_items = sum(
            1 for ex in self.executions if ex.status == "ABORTED"
        )

        if durations:
            self.stats.min_duration = min(durations)
            self.stats.max_duration = max(durations)
            self.stats.total_duration = sum(durations, timedelta())
            self.stats.avg_duration = self.stats.total_duration / len(durations)
