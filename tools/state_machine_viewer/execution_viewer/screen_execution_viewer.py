"""
Execution Viewer Screen for AWS Step Functions
"""

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
    TabbedContent,
    TabPane,
)

from ..api import get_execution_details
from ..api.api_requests import get_step_functions_client
from ..models import ExecutionDetails
from .tab_map_summary import MapRunsTab
from .tab_payloads import PayloadsTab
from .tab_steps import StepsTab
from .tab_summary import SummaryTab


class ExecutionViewerScreen(Screen[None]):
    """Screen for viewing execution details"""

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
    map_executions = reactive(None)

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
            with TabPane("Map Runs", id="map-runs-pane"):
                yield MapRunsTab(id="map-runs-container")
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
            client = get_step_functions_client(self.profile)
            self.execution_details = get_execution_details(
                client, self.state_machine_arn, self.execution_id
            )
            loading = self.query_one("#loading", LoadingIndicator)
            loading.display = False
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.app.notify(f"Error loading execution details: {e}", severity="error")

    def _refresh_tabs(self) -> None:
        """Refresh all tabs with current data."""
        if not self.execution_details:
            return
        self.app.run_worker(
            self.query_one(SummaryTab).refresh_data(self.execution_details)
        )
        self.query_one(StepsTab).refresh_data(self.execution_details)
        self.query_one(PayloadsTab).update_payloads(self.execution_details)
        self.query_one(MapRunsTab).refresh_data(self.execution_details)
