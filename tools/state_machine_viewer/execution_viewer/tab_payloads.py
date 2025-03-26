"""
Payloads
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Markdown, Static

from ..helpers import wrap_for_markdown
from ..models import ExecutionDetails


class PayloadsTab(Container):
    """Widget for displaying input and output payload information."""

    def compose(self) -> ComposeResult:
        """Compose the payloads tab layout."""

        yield Horizontal(
            Vertical(
                Static(
                    "Input Data Truncated by AWS",
                    id="input-truncated-notice",
                    classes="hidden",
                ),
                VerticalScroll(
                    Markdown("", id="input-data"),
                    id="input-container",
                ),
            ),
            Vertical(
                Static(
                    "Output Data Truncated by AWS",
                    id="output-truncated-notice",
                    classes="hidden",
                ),
                VerticalScroll(
                    Markdown("", id="output-data"),
                    id="output-container",
                    classes="hidden",
                ),
            ),
        )

    def update_section(
        self, data: str, truncated: bool, notice_id: str, data_id: str
    ) -> None:
        """Update a section with data and show/hide truncation notice."""
        notice = self.query_one(notice_id, Static)
        if truncated:
            notice.add_class("hidden")
        else:
            notice.remove_class("hidden")

        self.query_one(data_id, Markdown).update(wrap_for_markdown(data))

    def update_payloads(self, execution_details: ExecutionDetails) -> None:
        """Update the payload data."""
        self.update_section(
            execution_details.describe.input,
            execution_details.describe.inputDetails.included,
            "#input-truncated-notice",
            "#input-data",
        )

        self.update_section(
            execution_details.describe.output,
            execution_details.describe.outputDetails.included,
            "#output-truncated-notice",
            "#output-data",
        )

        self.query_one("#output-data", Markdown).update(
            wrap_for_markdown(execution_details.describe.output)
        )
