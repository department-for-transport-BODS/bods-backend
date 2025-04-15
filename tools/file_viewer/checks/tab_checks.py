"""
Checks for the dataset
"""

from pydantic import BaseModel
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import Button, Label, ListItem, ListView

from .check_model import Check, CheckInputData, CheckOutputData


def create_list_item(item: Check[CheckInputData, CheckOutputData]) -> ListItem:
    """
    The list data info
    """
    if item.result is None:
        symbol = "?"
        color = "grey"
    else:
        symbol = "✓" if item.result else "✗"
        color = "green" if item.result else "red"
    label = Label(f"{symbol} {item.name}")
    label.styles.color = color
    return ListItem(label, name=item.name)


class ChecksTab(Container):
    """
    Journey Information Tab
    """

    active_chk: reactive[Check[CheckInputData, CheckOutputData] | None] = reactive(  # type: ignore
        None
    )
    check_results: reactive[dict[str, BaseModel]] = reactive({})

    def __init__(
        self,
        checks: list[Check[CheckInputData, CheckOutputData]],
        data: CheckInputData,
    ):
        super().__init__()
        self.data = data
        self.checks = checks

    def refresh_check_list(self):
        """
        The try-except is for when the compose hasn't run but data exists
        """
        try:
            check_list = self.query_one("#check_list", ListView)
            check_list.clear()
            check_list.extend(create_list_item(item) for item in self.checks)
        except NoMatches:
            pass

    def run_checks(self):
        """
        Execute each check
        """
        for check in self.checks:
            check_output_data = check.check_func(self.data)
            self.check_results[check.name] = check_output_data
            check.result = check_output_data.result

    def compose(self) -> ComposeResult:
        yield Container(
            Button("Run Checks"),
            Horizontal(
                ListView(
                    *[create_list_item(item) for item in self.checks],
                    id="check_list",
                ),
                Container(
                    id="check_details_container",
                ),
            ),
        )

    def on_button_pressed(self, _event: Button.Pressed) -> None:
        """
        Since checks can take a while, run them on click
        """
        self.run_checks()
        self.update_check_details()
        self.refresh_check_list()

    def on_list_view_selected(self, message: ListView.Selected) -> None:
        """
        Sets the selected check
        """
        self.active_chk = next(
            (item for item in self.checks if item.name == message.item.name),
            None,
        )

    def watch_selected_check(
        self,
        _old_check: Check[CheckInputData, CheckOutputData],
        _new_check: Check[CheckInputData, CheckOutputData],
    ) -> None:
        """
        Textual Reactive Watch Function when selected_check variable changes
        """
        self.update_check_details()

    def watch_check_results(
        self,
    ):
        """
        Textual Reactive Watch function for when check_results changes
        """
        self.refresh_check_list()

    def update_check_details(self):
        """
        Update the right hand section with the details
        """

        check_details_container = self.query_one("#check_details_container", Container)
        check_details_container.remove_children()

        if self.active_chk:
            check_output_data = self.check_results.get(self.active_chk.name)
            if check_output_data:
                check_details_container.mount(
                    self.active_chk.detail_func(check_output_data)
                )
            else:
                check_details_container.mount(
                    Label("No details available for this check.")
                )
