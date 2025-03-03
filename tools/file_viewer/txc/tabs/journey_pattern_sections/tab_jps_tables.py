"""
Table Creation Functions
"""

from textual.widgets import DataTable

from tools.file_viewer.txc.utils_tables import TableConfig, create_data_table


def journey_pattern_timing_links_table() -> DataTable:
    """
    Table of Journey Pattern Timing Links for the selected Journey Pattern Section
    """
    return create_data_table(
        TableConfig(
            name="Journey Pattern Timing Links",
            table_id="table-journey-pattern-timing-links",
            columns=[
                "ID",
                "From Stop",
                "To Stop",
                "Route Link Ref",
                "Run Time",
                "WaitTime",
                "Distance",
                "Sequence",
            ],
            min_height=40,
            show_cursor=True,
            cursor_type="row",
        )
    )


def route_link_table() -> DataTable:
    """
    Route Link Details Table
    """
    return create_data_table(
        TableConfig(
            name="Route Link Details",
            table_id="table-route-link",
            columns=[
                "ID",
                "From Stop",
                "To Stop",
                "Distance",
            ],
            min_height=20,
        )
    )


def from_stop_table() -> DataTable:
    """
    From Stop Details Table
    """
    return create_data_table(
        TableConfig(
            name="From Stop Details",
            table_id="table-from-stop",
            columns=[
                "Stop Point Ref",
                "Wait Time",
                "Activity",
                "Timing Status",
                "Sequence Number",
            ],
            min_height=3,
            height=3,
            max_height=3,
        )
    )


def to_stop_table() -> DataTable:
    """
    To Stop Details Table
    """
    return create_data_table(
        TableConfig(
            name="To Stop Details",
            table_id="table-to-stop",
            columns=[
                "Stop Point Ref",
                "Wait Time",
                "Activity",
                "Timing Status",
                "Sequence Number",
            ],
            min_height=3,
            height=3,
            max_height=3,
        )
    )
