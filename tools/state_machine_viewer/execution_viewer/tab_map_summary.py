"""
Map Summary
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.reactive import var
from textual.widgets import DataTable

from tools.state_machine_viewer.api.api_requests import MapRunDescribe, MapRunInfo
from tools.state_machine_viewer.helpers import format_duration
from tools.state_machine_viewer.models import ExecutionDetails
from tools.state_machine_viewer.models.models_map_runs import (
    ExecutionCounts,
    ItemCounts,
)


class MapRunsTab(Container):
    """Widget for displaying map run information."""

    execution_details = var(None)
    selected_map_run = var(None)

    def compose(self) -> ComposeResult:
        """Compose the map runs tab layout."""
        yield DataTable(id="map-runs", cursor_type="row")

        with ScrollableContainer(id="details-container"):
            with Horizontal(id="details-row"):
                yield DataTable(id="general-info-table")
                yield DataTable(id="item-counts-table")
                yield DataTable(id="execution-counts-table")

    def on_mount(self) -> None:
        """Initialize the data tables."""
        # Main map runs table
        main_table: DataTable[str] = self.query_one("#map-runs", DataTable)
        main_table.add_column("Map Run ID", width=40)
        main_table.add_column("Start Time", width=25)
        main_table.add_column("End Time", width=25)
        main_table.add_column("Duration", width=15)
        main_table.add_column("Status", width=15)
        main_table.add_column("Items", width=10)
        main_table.add_column("Success", width=10)
        main_table.add_column("Failed", width=10)

        self._setup_general_info_table()
        self._setup_item_counts_table()
        self._setup_execution_counts_table()

        # Hide the details container initially
        details_container = self.query_one("#details-container", ScrollableContainer)
        details_container.display = False

    def _setup_general_info_table(self) -> None:
        """Setup the general info data table."""
        table: DataTable[str] = self.query_one("#general-info-table", DataTable)
        table.add_column("Property")
        table.add_column("Value")
        table.cursor_type = "none"
        table.zebra_stripes = True
        table.styles.width = "33%"

    def _setup_item_counts_table(self) -> None:
        """Setup the item counts data table."""
        table: DataTable[str] = self.query_one("#item-counts-table", DataTable)
        table.add_column("Item Metric")
        table.add_column("Count")
        table.cursor_type = "none"
        table.zebra_stripes = True
        table.styles.width = "33%"

    def _setup_execution_counts_table(self) -> None:
        """Setup the execution counts data table."""
        table: DataTable[str] = self.query_one("#execution-counts-table", DataTable)
        table.add_column("Execution Metric")
        table.add_column("Count")
        table.cursor_type = "none"
        table.zebra_stripes = True
        table.styles.width = "33%"

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
                map_run.listing.mapRunArn.split(":")[-1]
                if ":" in map_run.listing.mapRunArn
                else map_run.listing.mapRunArn
            )

            duration_str = format_duration(map_run.listing.duration)

            # Get stats from describe
            status = map_run.describe.status
            total_items = map_run.describe.itemCounts.total
            succeeded = map_run.describe.itemCounts.succeeded
            failed = map_run.describe.itemCounts.failed

            table.add_row(
                run_id,
                map_run.listing.startDate.strftime("%Y-%m-%d %H:%M:%S"),
                (
                    map_run.listing.stopDate.strftime("%Y-%m-%d %H:%M:%S")
                    if map_run.listing.stopDate
                    else "Running"
                ),
                duration_str,
                status,
                str(total_items),
                str(succeeded),
                str(failed),
                key=map_run.listing.mapRunArn,
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in the data table."""
        if event.data_table.id != "map-runs":  # type: ignore
            return

        map_run_arn = event.row_key.value

        if self.execution_details:
            for map_run in self.execution_details.map_runs:
                if map_run.listing.mapRunArn == map_run_arn:
                    self.selected_map_run = map_run
                    self._show_details(map_run)
                    break

    def _show_details(self, map_run_info: MapRunInfo) -> None:
        """Show detailed information for the selected map run."""
        details_container = self.query_one("#details-container", ScrollableContainer)
        details_container.display = True

        # Get describe data
        describe = map_run_info.describe

        # Update the three detail tables
        self._populate_general_info_table(describe)
        self._populate_item_counts_table(describe.itemCounts)
        self._populate_execution_counts_table(describe.executionCounts)

    def _populate_general_info_table(self, describe: MapRunDescribe) -> None:
        """Populate the general info data table."""
        table: DataTable[str] = self.query_one("#general-info-table", DataTable)
        table.clear()

        # Add a title row
        table.add_row("Map Run Information", "")

        table.add_row("Status", describe.status)
        table.add_row("Max Concurrency", str(describe.maxConcurrency))

        if describe.toleratedFailurePercentage is not None:
            table.add_row(
                "Tolerated Failure %", f"{describe.toleratedFailurePercentage}%"
            )

        if describe.toleratedFailureCount is not None:
            table.add_row(
                "Tolerated Failure Count", str(describe.toleratedFailureCount)
            )

        table.add_row("Redrive Count", str(describe.redriveCount))

        if describe.redriveDate:
            table.add_row(
                "Last Redriven", describe.redriveDate.strftime("%Y-%m-%d %H:%M:%S")
            )

    def _populate_item_counts_table(self, item_counts: ItemCounts) -> None:
        """Populate the item counts data table."""
        table: DataTable[str] = self.query_one("#item-counts-table", DataTable)
        table.clear()

        table.add_row("Item Counts", "")

        for field_name, value in item_counts.model_dump().items():
            display_name = " ".join(word.capitalize() for word in field_name.split("_"))
            table.add_row(display_name, str(value))

    def _populate_execution_counts_table(
        self, execution_counts: ExecutionCounts
    ) -> None:
        """Populate the execution counts data table."""
        table: DataTable[str] = self.query_one("#execution-counts-table", DataTable)
        table.clear()

        table.add_row("Execution Counts", "")

        for field_name, value in execution_counts.model_dump().items():
            display_name = " ".join(word.capitalize() for word in field_name.split("_"))
            table.add_row(display_name, str(value))
