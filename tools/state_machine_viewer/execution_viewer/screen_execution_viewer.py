"""
Execution Viewer Screen for AWS Step Functions
"""

import boto3
from mypy_boto3_stepfunctions.client import SFNClient
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    LoadingIndicator,
    Static,
    TabbedContent,
    TabPane,
)

from ..api_requests import get_execution_details
from ..helpers import format_duration
from ..models import ExecutionDetails
from .excution_viewer_calculations import enrich_execution_with_history
from .tab_map_info import MapExecutionsTab
from .tab_payloads import PayloadsTab
from .tab_steps import StepsTab
from .tab_summary import SummaryTab


class ExecutionViewerScreen(Screen[None]):
    """Screen for viewing execution details"""

    # Custom message for navigation
    class NavigateBack(Message):
        """Message sent when the user wants to go back to execution selection"""

    BINDINGS = [
        Binding("escape", "navigate_back", "Back to selection", show=True),
        Binding("q", "app.quit", "Quit", show=True),
        Binding("d", "toggle_dark", "Toggle dark mode", show=True),
        Binding("s", "sort_by_duration", "Sort by duration", show=True),
        Binding("n", "sort_by_name", "Sort by name", show=True),
        Binding("r", "refresh", "Refresh", show=True),
    ]

    execution_details = reactive(None)

    def __init__(self, state_machine_arn: str, execution_id: str, profile: str):
        self.state_machine_arn = state_machine_arn
        self.execution_id = execution_id
        self.profile = profile
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        yield Header(show_clock=True)
        yield LoadingIndicator(id="loading")

        with TabbedContent(initial="summary-pane"):
            with TabPane("Summary", id="summary-pane"):
                yield SummaryTab(id="summary-container")
            with TabPane("Steps", id="steps-pane"):
                yield StepsTab(id="steps-container")
            with TabPane("Payloads", id="payloads-pane"):
                yield PayloadsTab(id="payloads-container", classes="hidden")
            with TabPane("Map Executions", id="map-executions-pane"):
                yield MapExecutionsTab(id="map-executions-container")
        yield Footer()

    def on_mount(self) -> None:
        """Load execution details when mounted"""

        self.refresh_execution_details()

    @on(Button.Pressed, "#back-button")
    def on_back_button_pressed(self) -> None:
        """Handle back button press"""
        self.post_message(self.NavigateBack())

    @on(Button.Pressed, "#refresh-button")
    def on_refresh_button_pressed(self) -> None:
        """Handle refresh button press"""
        self.refresh_execution_details()

    def action_navigate_back(self) -> None:
        """Action to navigate back"""
        self.post_message(self.NavigateBack())

    def action_refresh(self) -> None:
        """Refresh execution details."""
        self.refresh_execution_details()

    def action_sort_by_duration(self) -> None:
        """Forward sort by duration action to steps tab."""
        steps_tab = self.query_one(StepsTab)
        steps_tab.action_sort_by_duration()

    def action_sort_by_name(self) -> None:
        """Forward sort by name action to steps tab."""
        steps_tab = self.query_one(StepsTab)
        steps_tab.action_sort_by_name()

    def watch_execution_details(
        self, execution_details: ExecutionDetails | None
    ) -> None:
        """Watch for changes to execution_details and update the UI"""
        if not execution_details:
            return

        # Update info section
        self.query_one("#execution-id", Static).update(
            f"Execution ID: {execution_details.name}"
        )
        self.query_one("#status", Static).update(f"Status: {execution_details.status}")
        self.query_one("#duration", Static).update(
            f"Total Duration: {format_duration(execution_details.duration)}"
        )

        map_run_arn = (
            execution_details.map_run_arn if execution_details.map_run_arn else "N/A"
        )
        self.query_one("#map-run-arn", Static).update(f"Map Run ARN: {map_run_arn}")

        error = execution_details.error
        cause = execution_details.cause

        if error or cause:
            error_title = "⚠️ Error Information ⚠️"
            error_content = f"{error_title}\n\nError: {error}\n\nCause:\n{cause}"
            self.query_one("#error-container").remove_class("hidden")
        else:
            error_content = ""
            self.query_one("#error-container").add_class("hidden")

        self.query_one("#error-data", Static).update(error_content)

        self._refresh_tabs()

    def refresh_execution_details(self) -> None:
        """Load execution details"""
        loading = self.query_one("#loading", LoadingIndicator)
        loading.display = True

        self.app.run_worker(
            self.fetch_execution_details_worker, name="fetch_execution_details"
        )

    async def fetch_execution_details_worker(self):
        """
        Worker to fetch details from AWS
        """
        try:
            client = self._get_step_functions_client()
            execution_details = get_execution_details(
                client, self.state_machine_arn, self.execution_id
            )
            execution_details = enrich_execution_with_history(execution_details, client)

            self.execution_details = execution_details
            loading = self.query_one("#loading", LoadingIndicator)
            loading.display = False
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.app.notify(f"Error loading execution details: {e}", severity="error")

    def _refresh_tabs(self) -> None:
        """Refresh all tabs with current data."""
        if not self.execution_details:
            return

        # Update Steps tab
        steps_tab = self.query_one(StepsTab)
        steps_tab.refresh_data(self.execution_details)

        # Update Payloads tab
        payloads_tab = self.query_one(PayloadsTab)
        payloads_tab.update_payloads(self.execution_details)

    def _get_step_functions_client(self) -> SFNClient:
        """Creates a boto3 Step Functions client."""
        session = boto3.Session(profile_name=self.profile)
        client: SFNClient = session.client("stepfunctions")  # type: ignore
        return client
