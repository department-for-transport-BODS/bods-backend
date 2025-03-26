"""
Summary Tab
"""

from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import var
from textual.widgets import Button, Static

from tools.state_machine_viewer.models import ExecutionDetails


class SummaryTab(Container):
    """
    Summary Default Page
    """

    execution_details = var(None)

    def compose(self) -> ComposeResult:
        """Compose the payloads tab layout."""

        yield Container(
            Container(
                Static("Execution ID: ", id="execution-id", classes="info-item"),
                Static("Status: ", id="status", classes="info-item"),
                Static("Total Duration: ", id="duration", classes="info-item"),
                Static("Map Run ARN: ", id="map-run-arn", classes="info-item"),
                id="execution-info",
            ),
            Container(
                Static("", id="error-data"),
                id="error-container",
            ),
            Container(
                Button("Back to Selection", id="back-button", variant="primary"),
                Button("Refresh Data", id="refresh-button"),
                id="button-container",
            ),
        )

    def refresh_data(self, execution_details: ExecutionDetails) -> None:
        """Refresh the data table with execution details."""
        self.execution_details = execution_details

        # Update info section
        self.query_one("#execution-id", Static).update(
            f"Execution ID: {execution_details.describe.name}"
        )
        self.query_one("#status", Static).update(
            f"Status: {execution_details.describe.status}"
        )
        self.query_one("#duration", Static).update(
            f"Total Duration: {execution_details.describe.duration}"
        )

        map_run_arn = execution_details.describe.executionArn

        self.query_one("#map-run-arn", Static).update(f"Map Run ARN: {map_run_arn}")

        error = "TBC"
        cause = "TBC"

        if error or cause:
            error_title = "⚠️ Error Information ⚠️"
            error_content = f"{error_title}\n\nError: {error}\n\nCause:\n{cause}"
            self.query_one("#error-container").remove_class("hidden")
        else:
            error_content = ""
            self.query_one("#error-container").add_class("hidden")

        self.query_one("#error-data", Static).update(error_content)
