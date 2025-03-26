"""
Steps Viewer
"""

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive, var
from textual.widgets import DataTable

from ..helpers import format_duration
from ..models import ExecutionDetails, HistoryEvent
from .models import StepDuration


def analyze_step_durations(events: list[HistoryEvent]) -> list[StepDuration]:
    """Analyzes events to calculate step durations."""
    step_start_times: dict[str, datetime] = {}
    step_durations: list[StepDuration] = []

    for event in events:
        state_name: str = (
            event.details.name if event.details and event.details.name else "Unknown"
        )
        if event.type.endswith("StateEntered"):
            step_start_times[state_name] = event.timestamp

        elif event.type.endswith("StateExited"):
            if state_name in step_start_times:
                start_time = step_start_times[state_name]
                step_durations.append(
                    StepDuration(
                        name=state_name,
                        duration=event.timestamp - start_time,
                        start_time=start_time,
                        end_time=event.timestamp,
                    )
                )
    return step_durations


class StepsTab(Container):
    """Widget for displaying step duration information."""

    sort_by = reactive("duration")
    execution_details = var(None)

    def compose(self) -> ComposeResult:
        """Compose the steps tab layout."""
        yield DataTable(id="step-durations", cursor_type="row")

    def on_mount(self) -> None:
        """Initialize the data table."""
        table: DataTable[str] = self.query_one("#step-durations", DataTable)
        table.add_column("Step Name", width=50)
        table.add_column("Duration", width=15)
        table.add_column("Start Time", width=25)
        table.add_column("End Time", width=25)

    def refresh_data(self, execution_details: ExecutionDetails) -> None:
        """Refresh the data table with execution details."""
        self.execution_details = execution_details
        self._refresh_table()

    def action_sort_by_duration(self) -> None:
        """Sort steps by duration."""
        self.sort_by = "duration"

    def action_sort_by_name(self) -> None:
        """Sort steps by name."""
        self.sort_by = "name"

    def watch_sort_by(self) -> None:
        """Watch for changes to sort_by and refresh the table."""
        self._refresh_table()

    def _refresh_table(self) -> None:
        """Refresh the table with current sort settings."""
        if not self.execution_details:
            return

        table: DataTable[str] = self.query_one(DataTable)
        table.clear()
        self._populate_table(table)

    def _populate_table(self, table: DataTable[str]) -> None:
        """Populate the table with sorted step data."""
        if not self.execution_details:
            return
        steps = analyze_step_durations(self.execution_details.history)
        if self.sort_by == "duration":
            sorted_steps = sorted(steps, key=lambda x: x.duration, reverse=True)
        else:
            sorted_steps = sorted(steps, key=lambda x: x.name)

        for step in sorted_steps:
            duration_str = format_duration(step.duration)
            table.add_row(
                step.name,
                duration_str,
                step.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                step.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                key=step.name,
            )
