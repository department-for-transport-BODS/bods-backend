"""
Table Creation Functions
"""

from typing import cast

from common_layer.xml.txc.models import TimingStatusT
from textual.widgets import DataTable

from ...utils_tables import TableConfig, create_data_table


def journey_pattern_timing_links_table() -> DataTable[str]:
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


def route_link_table() -> DataTable[str]:
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


def from_stop_table() -> DataTable[str | TimingStatusT | None]:
    """
    From Stop Details Table
    """
    return cast(
        DataTable[str | TimingStatusT | None],
        create_data_table(
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
        ),
    )


def to_stop_table() -> DataTable[str | TimingStatusT | None]:
    """
    To Stop Details Table
    """
    return cast(
        DataTable[str | TimingStatusT | None],
        create_data_table(
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
        ),
    )
