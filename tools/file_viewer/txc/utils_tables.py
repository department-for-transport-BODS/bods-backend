"""
Table Factory
"""

from pydantic import BaseModel, Field
from textual.widgets import DataTable
from textual.widgets.data_table import CursorType


class TableConfig(BaseModel):
    """Configuration model for DataTable widgets in Textual."""

    name: str = Field(..., description="Display name of the table")
    table_id: str = Field(..., description="ID to assign to the table for querying")
    columns: list[str] = Field(..., description="List of column headers")
    min_height: int = Field(default=20, description="Minimum height for the table")
    height: int | None = Field(
        default=None, description="Exact height for the table (if specified)"
    )
    max_height: int | None = Field(
        default=None, description="Maximum height for the table"
    )
    show_cursor: bool = Field(default=False, description="Whether to show cursor")
    cursor_type: CursorType = Field(
        default="row", description="Type of cursor (row or cell)"
    )


def create_data_table(config: TableConfig) -> DataTable[str]:
    """
    Factory function to create a DataTable with consistent styling and configuration.

    """
    table: DataTable[str] = DataTable(
        show_header=True,
        show_row_labels=True,
        zebra_stripes=True,
        header_height=1,
        show_cursor=config.show_cursor,
        cursor_type=config.cursor_type,
        name=config.name,
        id=config.table_id,
    )

    table.styles.min_height = config.min_height
    if config.height is not None:
        table.styles.height = config.height
    if config.max_height is not None:
        table.styles.max_height = config.max_height

    table.add_columns(*config.columns)

    return table
