"""
Tables for Routes Tab
"""

from textual.widgets import DataTable

from tools.file_viewer.txc.utils_tables import TableConfig, create_data_table


def route_sections_list() -> DataTable:
    """
    Table of Route Sections for the selected route
    """
    config = TableConfig(
        name="Route Sections",
        table_id="table-route-sections",
        columns=[
            "ID",
            "Number of Route Links",
        ],
        min_height=40,
        show_cursor=True,
        cursor_type="row",
    )
    return create_data_table(config)


def route_links_table() -> DataTable:
    """
    Route Links table
    """
    config = TableConfig(
        name="Route Links",
        table_id="table-route-links",
        columns=[
            "ID",
            "From",
            "From Name",
            "To",
            "To Name",
            "Distance",
        ],
        min_height=20,
        show_cursor=True,
        cursor_type="row",
    )
    return create_data_table(config)
