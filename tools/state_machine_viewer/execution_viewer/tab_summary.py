from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button, Static


class SummaryTab(Container):
    """
    Summary Default Page
    """

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
