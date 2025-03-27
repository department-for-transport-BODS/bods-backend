"""
State Machine Viewer - Main application with persistent header
"""

import typer
from structlog.stdlib import get_logger
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import Header

from .execution_selector import ExecutionSelectorScreen
from .execution_viewer import ExecutionViewerScreen
from .state_machine_selector import StateMachineSelectorScreen

log = get_logger()

app = typer.Typer()


class StepFunctionViewerApp(App[None]):
    """A Textual App to display AWS Step Functions execution data."""

    TITLE = "AWS Step Functions Execution Viewer"
    SUB_TITLE = "Interactive viewer for step function executions"

    HEADER = Header(show_clock=True)

    CSS = """
    #execution-info {
        layout: horizontal;
        background: $surface;
        padding: 1;
        border-bottom: solid $primary;
    }
    .info-item {
        width: 1fr;
        content-align: center middle;
    }
    #step-durations {
        height: 1fr;
    }
    .duration-cell {
        text-align: right;
    }
    #loading-container {
        height: 100%;
        align: center middle;
    }
    #selector-container {
        padding: 2;
    }
    #selectors-container {
        margin: 2 0;
    }
    #title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }
    #subtitle {
        text-align: center;
        color: $text-disabled;
        padding-bottom: 1;
    }
    #button-container {
        layout: horizontal;
        height: auto;
        margin: 1 0;
    }
    .selector-label {
        text-align: center;
        margin-top: 1;
        margin-bottom: 1;
    }
    """

    # Reactive attributes to store execution details
    state_machine_arn = reactive("")
    execution_id = reactive("")
    profile = reactive("default")

    def __init__(
        self,
        state_machine_arn: str | None = None,
        execution_id: str | None = None,
        profile: str = "default",
    ):
        super().__init__()
        if state_machine_arn:
            self.state_machine_arn = state_machine_arn
        if execution_id:
            self.execution_id = execution_id
        self.profile = profile

    def compose(self) -> ComposeResult:
        """Compose the app layout with a permanent header"""
        yield self.HEADER

    def on_mount(self) -> None:
        """Handle app mount - check if we need selection or direct load"""
        if self.state_machine_arn and self.execution_id:
            self.show_execution_details()
        else:
            self.show_state_machine_selector()

    def show_state_machine_selector(self) -> None:
        """Show the state_machine selector screen"""
        self.push_screen(StateMachineSelectorScreen())

    def show_execution_selector(self, state_machine_arn: str) -> None:
        """Show the execution selector screen"""
        self.push_screen(ExecutionSelectorScreen(state_machine_arn, self.profile))

    def show_execution_details(self) -> None:
        """Show the execution details screen"""
        self.clear_screens()

        self.push_screen(
            ExecutionViewerScreen(
                self.state_machine_arn, self.execution_id, self.profile
            )
        )

    def clear_screens(self) -> None:
        """Clear all screens except for the app screen"""
        while len(self._screen_stack) > 1:
            try:
                self.pop_screen()
            except Exception:  # pylint: disable=broad-exception-caught
                break

    def on_state_machine_selector_screen_selection_complete(
        self, message: StateMachineSelectorScreen.SelectionComplete
    ) -> None:
        """Handle state_machine selection completion"""
        self.state_machine_arn = message.state_machine_arn
        self.show_execution_selector(message.state_machine_arn)

    def on_execution_selector_screen_execution_selected(
        self, message: ExecutionSelectorScreen.ExecutionSelected
    ) -> None:
        """Handle execution selection"""
        self.state_machine_arn = message.state_machine_arn
        self.execution_id = message.execution_id
        self.show_execution_details()

    def on_execution_viewer_navigate_back(
        self, _message: ExecutionViewerScreen.NavigateBack
    ) -> None:
        """Handle navigation back from execution details"""
        self.clear_screens()
        self.show_state_machine_selector()


@app.command()
def check_execution(
    state_machine_arn: str = typer.Argument(
        None, help="ARN of the state machine to check"
    ),
    execution_id: str = typer.Argument(None, help="Execution ID to check"),
    profile: str = typer.Option("default", "--profile", "-p", help="AWS profile name"),
) -> None:
    """Checks and displays information for an AWS Step Functions execution."""
    step_function_app = StepFunctionViewerApp(
        state_machine_arn=state_machine_arn,
        execution_id=execution_id,
        profile=profile,
    )
    step_function_app.run()


if __name__ == "__main__":
    app()
