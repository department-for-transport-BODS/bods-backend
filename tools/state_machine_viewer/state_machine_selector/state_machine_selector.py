"""
State Machine and Environment Selector screen
"""

from typing import cast

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Container, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Header, Label, Select

STATE_MACHINES: dict[str, dict[str, str]] = {
    "timetables": {
        "dev": "arn:aws:states:eu-west-2:228266753808:stateMachine:bods-backend-dev-tt-sm",
        "test": "arn:aws:states:eu-west-2:228266753808:stateMachine:bods-backend-test-tt-sm",
        "uat": "arn:aws:states:eu-west-2:228266753808:stateMachine:bods-backend-uat-tt-sm",
    }
}


def get_state_machine_arn(machine_type: str, environment: str) -> str | None:
    """
    Get the ARN for a specific state machine type and environment

    """
    if machine_type in STATE_MACHINES and environment in STATE_MACHINES[machine_type]:
        return STATE_MACHINES[machine_type][environment]
    return None


class EnvironmentOption:
    """
    Rich renderable for environment options in a select widget.
    Displays the environment name on the first line and ARN on the second line.
    """

    def __init__(self, name: str, env_id: str, arn: str):
        """
        Initialize an environment option

        Args:
            name: Display name (e.g., "Development")
            env_id: Environment ID (e.g., "dev")
            arn: The full ARN for this environment
        """
        self.name = name
        self.env_id = env_id
        self.arn = arn

    def __rich__(self) -> Text:
        """
        Rich renderable method

        Returns:
            A text object with the formatted environment option
        """
        text = Text()
        text.append(f"{self.name}\n", style="bold")
        text.append(self.arn, style="dim")
        return text


class StateMachineSelectorScreen(Screen[None]):
    """Screen for selecting both state machine type and environment on one page"""

    SUB_TITLE = "State Machine Selection"

    class SelectionComplete(Message):
        """Message sent when both selections are complete"""

        def __init__(self, state_machine_arn: str) -> None:
            self.state_machine_arn = state_machine_arn
            super().__init__()

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", show=True),
    ]

    def __init__(self):
        self.selected_type = "timetables"  # Default selection
        self.selected_environment = "dev"  # Default environment
        super().__init__()

    def compose(self) -> ComposeResult:
        state_machine_options = [("Serverless Timetables", "timetables")]

        # Create Rich renderables for environment options
        environment_options: list[tuple[EnvironmentOption, str]] = []
        for env_name, env_id in [
            ("Development", "dev"),
            ("Test", "test"),
            ("UAT", "uat"),
        ]:
            arn = (
                get_state_machine_arn("timetables", env_id)
                or f"Unknown ARN for {env_id}"
            )
            option = EnvironmentOption(env_name, env_id, arn)
            environment_options.append((option, env_id))

        yield Container(
            Header(show_clock=True),
            Vertical(
                Label("State Machine Type", classes="selector-label"),
                Center(
                    Select(
                        state_machine_options,
                        id="state-machine-type",
                        prompt="Select a state machine type",
                        value="timetables",
                    )
                ),
                Label("Environment", classes="selector-label"),
                Center(
                    Select(
                        environment_options,
                        id="environment",
                        prompt="Select an environment",
                        value="dev",
                    )
                ),
                Button(
                    "Continue", id="continue-button", variant="primary", disabled=False
                ),
                id="selectors-container",
            ),
            id="selector-container",
        )

    def on_mount(self) -> None:
        """Set default selections and ensure continue button is enabled"""
        state_machine_select: Select[str] = self.query_one(
            "#state-machine-type", Select
        )
        environment_select: Select[str] = self.query_one("#environment", Select)

        state_machine_select.value = "timetables"
        environment_select.value = "dev"

        button = self.query_one("#continue-button", Button)
        button.disabled = False

    @on(Select.Changed, "#state-machine-type")
    def on_state_machine_selected(self, event: Select.Changed) -> None:
        """Handle selection of a state machine type"""
        if event.value == Select.BLANK:
            return

        self.selected_type = cast(str, event.value)
        self._check_continue_button()

    @on(Select.Changed, "#environment")
    def on_environment_selected(self, event: Select.Changed) -> None:
        """Handle selection of an environment"""
        if event.value == Select.BLANK:
            return

        self.selected_environment = cast(str, event.value)
        self._check_continue_button()

    def _check_continue_button(self) -> None:
        """Enable continue button if both selections are made"""
        button = self.query_one("#continue-button", Button)
        button.disabled = not (self.selected_type and self.selected_environment)

    @on(Button.Pressed, "#continue-button")
    def on_continue(self) -> None:
        """Handle continue button press"""
        if self.selected_type and self.selected_environment:
            arn = self._generate_arn(self.selected_environment)
            self.post_message(self.SelectionComplete(arn))

    def _generate_arn(self, environment: str) -> str:
        """Generate the state machine ARN based on selection"""
        # Use our simple dictionary lookup function
        arn = get_state_machine_arn(self.selected_type, environment)
        return arn or ""
