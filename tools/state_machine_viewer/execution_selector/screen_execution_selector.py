"""
Select an Execution for the selected state machine
"""

from typing import cast

import boto3
from mypy_boto3_stepfunctions.client import SFNClient
from mypy_boto3_stepfunctions.type_defs import ExecutionListItemTypeDef
from structlog.stdlib import get_logger
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Header, Label, LoadingIndicator, Select, Static

log = get_logger(__name__)


class ExecutionSelectorScreen(Screen[None]):
    """Screen for selecting a state machine execution"""

    SUB_TITLE = "Execution Selection"

    class ExecutionSelected(Message):
        """Message sent when an execution is selected"""

        def __init__(self, execution_id: str, state_machine_arn: str) -> None:
            self.execution_id = execution_id
            self.state_machine_arn = state_machine_arn
            super().__init__()

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", show=True),
        Binding("r", "refresh", "Refresh", show=True),
    ]

    def __init__(self, state_machine_arn: str, profile: str):
        self.state_machine_arn = state_machine_arn
        self.profile = profile
        self.executions: list[ExecutionListItemTypeDef] = []
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Container(
            Header(show_clock=True),
            Label("Select Execution", id="title"),
            Label(f"State Machine: {self.state_machine_arn}", id="subtitle"),
            LoadingIndicator(id="loading"),
            Static(id="executions-container"),
            Button(
                "Back to Environment Selection", id="back-to-env", variant="primary"
            ),
            id="selector-container",
        )

    def on_mount(self) -> None:
        """When screen is mounted, fetch executions"""
        # Start the fetch operation without nesting workers
        self.refresh_executions()

    def action_refresh(self) -> None:
        """Refresh the executions list"""
        self.refresh_executions()

    def refresh_executions(self) -> None:
        """Start the execution fetch operation in a worker"""
        loading = self.query_one("#loading", LoadingIndicator)
        loading.display = True

        container = self.query_one("#executions-container", Static)
        container.display = False

        # Run fetch executions in a worker
        self.app.run_worker(self._fetch_executions_worker, name="fetch_executions")

    @on(Button.Pressed, "#back-to-env")
    def on_back_button_pressed(self) -> None:
        """Handle back button press"""
        self.app.pop_screen()

    async def _fetch_executions_worker(self) -> None:
        """Worker function to fetch executions and update UI"""
        try:
            client = self._get_step_functions_client()
            response = client.list_executions(
                stateMachineArn=self.state_machine_arn, maxResults=10
            )
            self.executions = response.get("executions", [])

            self.update_executions_list()
        except Exception as e:  # pylint: disable=broad-exception-caught
            log.error("Error fetching executions: {e}", exc_info=True)

            # Show error in UI
            container = self.query_one("#executions-container", Static)
            container.remove_children()
            container.mount(Label(f"Error: {e}"))
            container.display = True

            loading = self.query_one("#loading", LoadingIndicator)
            loading.display = False

    def update_executions_list(self) -> None:
        """Update the UI with fetched executions"""
        container = self.query_one("#executions-container", Static)
        loading = self.query_one("#loading", LoadingIndicator)

        if not self.executions:
            container.remove_children()
            container.mount(Label("No executions found"))
            container.display = True
            loading.display = False
            return

        # Create select options from executions
        options: list[tuple[str, str]] = []
        for execution in self.executions:
            start_time = execution["startDate"]
            name = execution["name"]
            status = execution["status"]

            # Format timestamp for display
            formatted_time = start_time.strftime("%Y-%m-%d %H:%M:%S")

            # Create a friendly label for the execution
            label = f"{formatted_time} - {name} ({status})"

            # Add to options
            options.append((label, name))

        # Create and add Select widget
        select = Select[str](
            options, id="executions-list", prompt="Select an execution"
        )
        container.remove_children()
        container.mount(select)
        container.display = True
        loading.display = False

    def _get_step_functions_client(self) -> SFNClient:
        """Creates a boto3 Step Functions client."""
        session = boto3.Session(profile_name=self.profile)
        client: SFNClient = session.client("stepfunctions")  # type: ignore
        return client

    @on(Select.Changed, "#executions-list")
    def on_execution_selected(self, event: Select.Changed) -> None:
        """Handle selection of an execution"""
        if event.value == Select.BLANK:
            return

        execution_id = cast(str, event.value)
        self.post_message(self.ExecutionSelected(execution_id, self.state_machine_arn))
