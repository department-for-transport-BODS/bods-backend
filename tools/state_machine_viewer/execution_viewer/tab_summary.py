"""
Summary Tab
"""

from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import var
from textual.widgets import Button, MarkdownViewer

from ..models import ExecutionDetails


def generate_execution_markdown(execution_details: ExecutionDetails) -> str:
    """
    Generate formatted markdown content from execution details.

    Args:
        execution_details: The execution details to format

    Returns:
        Formatted markdown string
    """
    status_emoji = {
        "RUNNING": "🔄",
        "SUCCEEDED": "✅",
        "FAILED": "❌",
        "ABORTED": "⏹️",
        "TIMED_OUT": "⏱️",
    }.get(execution_details.describe.status, "❓")

    md = f"""
# Execution Summary

## Basic Information

| - | - |
|----------|-------|
| **Execution ID** | `{execution_details.describe.name}` |
| **Status** | {status_emoji} **{execution_details.describe.status}** |
| **Duration** | ⏱️ `{execution_details.describe.duration}` |
| **Started At** | {execution_details.describe.startDate.strftime('%Y-%m-%d %H:%M:%S')} |
| **Completed At** | {execution_details.describe.stopDate.strftime('%Y-%m-%d %H:%M:%S')} |

## Execution Details

- **State Machine ARN**: `{execution_details.describe.stateMachineArn}`
- **Execution ARN**: `{execution_details.describe.executionArn}`
- **Redrive Count**: {execution_details.describe.redriveCount}
- **Redrive Status**: {execution_details.describe.redriveStatus}
"""

    md += f"""
## Additional Information

- **Trace Header**: 
`{execution_details.describe.traceHeader}`
- **Input Details**: 
`{"Included" if execution_details.describe.inputDetails.included else "Not Included"}`
- **Output Details**: 
`{"Included" if execution_details.describe.outputDetails.included else "Not Included"}`
"""

    return md


class SummaryTab(Container):
    """
    Summary Tab showing execution details with a Markdown viewer
    """

    execution_details = var(None)

    def compose(self) -> ComposeResult:
        """Compose the summary tab layout."""
        yield Container(
            MarkdownViewer(show_table_of_contents=False, id="execution-summary"),
            Container(
                Button("Back to Selection", id="back-button", variant="primary"),
                Button("Refresh Data", id="refresh-button"),
                id="button-container",
            ),
        )

    async def on_mount(self) -> None:
        """Initialize the widget when mounted."""
        markdown_viewer = self.query_one("#execution-summary", MarkdownViewer)
        await markdown_viewer.document.update("Loading execution details...")

    async def refresh_data(self, execution_details: ExecutionDetails) -> None:
        """Refresh the data with execution details formatted as markdown."""
        self.execution_details = execution_details

        markdown_content = generate_execution_markdown(execution_details)

        markdown_viewer = self.query_one("#execution-summary", MarkdownViewer)
        await markdown_viewer.document.update(markdown_content)
