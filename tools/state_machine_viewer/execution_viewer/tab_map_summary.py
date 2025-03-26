"""
Map Summary
"""

from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import var
from textual.widgets import DataTable

from tools.state_machine_viewer.helpers import format_duration

from ..models import ExecutionDetails


class MapRunsTab(Container):
    """Widget for displaying map run information."""

    execution_details = var(None)

    def compose(self) -> ComposeResult:
        """Compose the map runs tab layout."""
        yield DataTable(id="map-runs", cursor_type="row")

    def on_mount(self) -> None:
        """Initialize the data table."""
        table: DataTable[str] = self.query_one("#map-runs", DataTable)
        table.add_column("Map Run ID", width=40)
        table.add_column("Start Time", width=25)
        table.add_column("End Time", width=25)
        table.add_column("Duration", width=15)

    def refresh_data(self, execution_details: ExecutionDetails) -> None:
        """Refresh the data table with execution details."""
        self.execution_details = execution_details
        self._refresh_table()

    def _refresh_table(self) -> None:
        """Refresh the table with map run data."""
        if not self.execution_details:
            return

        table: DataTable[str] = self.query_one("#map-runs", DataTable)
        table.clear()
        self._populate_table(table)

    def _populate_table(self, table: DataTable[str]) -> None:
        """Populate the table with map run data."""
        if not self.execution_details:
            return

        map_runs = self.execution_details.map_runs

        for map_run in map_runs:
            run_id = (
                map_run.mapRunArn.split(":")[-1]
                if ":" in map_run.mapRunArn
                else map_run.mapRunArn
            )

            duration_str = format_duration(map_run.duration)
            table.add_row(
                run_id,
                map_run.startDate.strftime("%Y-%m-%d %H:%M:%S"),
                map_run.stopDate.strftime("%Y-%m-%d %H:%M:%S"),
                duration_str,
                key=map_run.mapRunArn,
            )
