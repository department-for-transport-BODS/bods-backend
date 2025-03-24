"""
Map Executions Tab Component for AWS Step Functions Execution Viewer
"""

from rich.console import RenderableType
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive, var
from textual.widgets import DataTable, Label, Select, Static

from ..helpers import format_duration
from .map_info_models import MapExecution, MapExecutionItem, MapRunStats


class MapStatsDisplay(Container):
    """Widget to display Map execution statistics."""

    map_stats: var[MapRunStats | None] = var(None)
    map_name: var[str] = var("Unknown Map")

    def compose(self) -> ComposeResult:
        """Compose the statistics display layout."""
        with Container(id="map-stats-container"):
            yield Static("Map State Statistics:", classes="section-title")

            with Horizontal(id="map-stats-grid"):
                # First column
                with Vertical(id="map-stats-col1", classes="stats-column"):
                    yield Static(
                        "Total Items: -", id="total-items", classes="stat-item"
                    )
                    yield Static(
                        "Succeeded: -", id="succeeded-items", classes="stat-item"
                    )
                    yield Static("Failed: -", id="failed-items", classes="stat-item")

                # Second column
                with Vertical(id="map-stats-col2", classes="stats-column"):
                    yield Static("Running: -", id="running-items", classes="stat-item")
                    yield Static("Pending: -", id="pending-items", classes="stat-item")
                    yield Static("Aborted: -", id="aborted-items", classes="stat-item")

                # Third column
                with Vertical(id="map-stats-col3", classes="stats-column"):
                    yield Static(
                        "Avg Duration: -", id="avg-duration", classes="stat-item"
                    )
                    yield Static(
                        "Min Duration: -", id="min-duration", classes="stat-item"
                    )
                    yield Static(
                        "Max Duration: -", id="max-duration", classes="stat-item"
                    )

    def watch_map_stats(self, stats: MapRunStats | None) -> None:
        """Update the statistics when map_stats changes."""
        if not stats:
            return

        # Update item counts
        self.query_one("#total-items", Static).update(
            f"Total Items: {stats.total_items}"
        )
        self.query_one("#succeeded-items", Static).update(
            f"Succeeded: {stats.succeeded_items} ({stats.success_percentage:.1f}%)"
        )
        self.query_one("#failed-items", Static).update(f"Failed: {stats.failed_items}")
        self.query_one("#running-items", Static).update(
            f"Running: {stats.running_items}"
        )
        self.query_one("#pending-items", Static).update(
            f"Pending: {stats.pending_items}"
        )
        self.query_one("#aborted-items", Static).update(
            f"Aborted: {stats.aborted_items}"
        )

        # Update durations
        self.query_one("#avg-duration", Static).update(
            f"Avg Duration: {format_duration(stats.avg_duration)}"
        )
        self.query_one("#min-duration", Static).update(
            f"Min Duration: {format_duration(stats.min_duration)}"
        )
        self.query_one("#max-duration", Static).update(
            f"Max Duration: {format_duration(stats.max_duration)}"
        )

    def watch_map_name(self, name: str) -> None:
        """Update the title when map_name changes."""
        self.query_one(".section-title", Static).update(f"Map State: {name}")


class MapExecutionsTab(Container):
    """Widget for displaying Map execution information."""

    sort_by = reactive("duration")
    sort_reverse = reactive(False)
    map_executions = var([])
    selected_execution_index = reactive(0)

    def compose(self) -> ComposeResult:
        """Compose the Map executions tab layout."""
        with Container(id="map-executions-container"):
            # Map execution selector (if multiple)
            with Horizontal(id="map-selector-container"):
                yield Label("Map Execution: ")
                yield Select([], id="map-execution-select")

            # Map statistics
            yield MapStatsDisplay(id="map-stats-display")

            # Map item list controls
            with Horizontal(id="map-controls-container"):
                yield Label("Sort by: ")
                yield Select(
                    [
                        ("Duration", "duration"),
                        ("Index", "index"),
                        ("Status", "status"),
                        ("Start Time", "start_time"),
                    ],
                    id="sort-select",
                    value="duration",
                )
                yield Static("↑", id="sort-direction")

            # Map items table
            yield DataTable(id="map-items-table")

    def on_mount(self) -> None:
        """Set up the data table when mounted."""
        # Set up the table
        table: DataTable[str] = self.query_one("#map-items-table", DataTable)
        table.add_column("Index", width=10)
        table.add_column("Status", width=15)
        table.add_column("Duration", width=15)
        table.add_column("Start Time", width=25)
        table.add_column("End Time", width=25)
        table.add_column("Error", width=25)

    def _toggle_sort_direction(self) -> None:
        """Toggle the sort direction."""
        self.sort_reverse = not self.sort_reverse
        self.query_one("#sort-direction", Static).update(
            "↓" if self.sort_reverse else "↑"
        )

    def _on_sort_changed(self, value: str) -> None:
        """Handle changes to the sort selection."""
        self.sort_by = value

    def _on_map_execution_changed(self, value: int) -> None:
        """Handle changes to the map execution selection."""
        self.selected_execution_index = int(value)

    def watch_map_executions(self) -> None:
        """Handle changes to the map_executions list."""
        if not self.map_executions:
            return

        # Update the map execution selector
        select: Select[int] = self.query_one("#map-execution-select", Select)
        options: list[tuple[RenderableType, int]] = []

        for i, execution in enumerate(self.map_executions):
            options.append((f"{execution.state_name}", i))

        select.set_options(options)
        select.value = 0

        # Show or hide selector based on number of map executions
        if len(self.map_executions) <= 1:
            self.query_one("#map-selector-container").add_class("hidden")
        else:
            self.query_one("#map-selector-container").remove_class("hidden")

        # Update the view with the first execution
        self._update_view()

    def watch_selected_execution_index(self) -> None:
        """Update the view when the selected execution changes."""
        self._update_view()

    def watch_sort_by(self) -> None:
        """Refresh the table when sort_by changes."""
        self._update_table()

    def watch_sort_reverse(self) -> None:
        """Refresh the table when sort_reverse changes."""
        self._update_table()

    def _update_view(self) -> None:
        """Update the view with the selected Map execution."""
        if not self.map_executions or self.selected_execution_index >= len(
            self.map_executions
        ):
            return

        # Get the selected Map execution
        execution = self.map_executions[self.selected_execution_index]

        # Update the stats display
        stats_display = self.query_one(MapStatsDisplay)
        stats_display.map_stats = execution.stats
        stats_display.map_name = execution.state_name

        # Update the table
        self._update_table()

    def _update_table(self) -> None:
        """Update the table with sorted execution items."""
        if not self.map_executions or self.selected_execution_index >= len(
            self.map_executions
        ):
            return

        # Get the selected Map execution
        execution = self.map_executions[self.selected_execution_index]

        # Sort the executions
        sorted_items = self._get_sorted_items(execution)

        # Update the table
        table: DataTable[str] = self.query_one("#map-items-table", DataTable)
        table.clear()

        for item in sorted_items:
            duration_str = format_duration(item.duration)
            start_time_str = (
                item.start_time.strftime("%Y-%m-%d %H:%M:%S")
                if item.start_time
                else "N/A"
            )
            end_time_str = (
                item.end_time.strftime("%Y-%m-%d %H:%M:%S") if item.end_time else "N/A"
            )

            # Truncate error message if needed
            error = item.error or ""
            if len(error) > 30:
                error = error[:27] + "..."

            table.add_row(
                str(item.index),
                item.status,
                duration_str,
                start_time_str,
                end_time_str,
                error,
                key=str(item.index),
            )

    def _get_sorted_items(self, execution: MapExecution) -> list[MapExecutionItem]:
        """Get sorted execution items based on current sort settings."""
        if self.sort_by == "duration":
            return sorted(
                execution.executions,
                key=lambda x: x.duration.total_seconds(),
                reverse=self.sort_reverse,
            )
        if self.sort_by == "index":
            return sorted(
                execution.executions, key=lambda x: x.index, reverse=self.sort_reverse
            )
        if self.sort_by == "status":
            return sorted(
                execution.executions, key=lambda x: x.status, reverse=self.sort_reverse
            )
        if self.sort_by == "start_time":
            return sorted(
                execution.executions,
                key=lambda x: x.start_time,
                reverse=self.sort_reverse,
            )

        return sorted(
            execution.executions, key=lambda x: x.duration.total_seconds(), reverse=True
        )

    def refresh_data(self, map_executions: list[MapExecution]) -> None:
        """Refresh the tab with new map execution data."""
        self.map_executions = map_executions
