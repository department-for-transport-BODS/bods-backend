"""
Table Definitions
"""

from textual.widgets import DataTable

from ...utils_tables import TableConfig, create_data_table


def journey_pattern_table() -> DataTable:
    """Journey Pattern Details Table"""
    config = TableConfig(
        name="Journey Pattern Details",
        table_id="table-journey-pattern",
        columns=[
            "ID",
            "Private Code",
            "Destination Display",
            "Operator Ref",
            "Direction",
            "Route Ref",
            "Description",
            "Layover Point",
        ],
    )
    return create_data_table(config)


def journey_pattern_sections_table() -> DataTable:
    """
    Journey Pattern Sections Table
    """
    table = DataTable(
        show_header=True,
        show_row_labels=True,
        zebra_stripes=True,
        header_height=1,
        name="Journey Pattern Sections",
        id="table-journey-pattern-sections",
    )
    table.styles.min_height = 20
    columns = [
        "Section Ref",
    ]
    table.add_columns(*columns)
    return table


def vehicle_journey_timing_links_table() -> DataTable:
    """Table of Vehicle Journey Timing Links for the selected Vehicle Journey"""
    config = TableConfig(
        name="Vehicle Journey Timing Links",
        table_id="table-vehicle-journey-timing-links",
        columns=[
            "ID",
            "JPTL Ref",
            "VJ Ref",
            "Run Time",
            "Wait Time",
            "Arrival",
            "Departure",
            "Sequence",
        ],
        min_height=40,
        show_cursor=True,
    )
    return create_data_table(config)


def route_table() -> DataTable:
    """
    Route Details Table
    """
    table = DataTable(
        show_header=True,
        show_row_labels=True,
        zebra_stripes=True,
        header_height=1,
        name="Route Details",
        id="table-route",
    )
    table.styles.min_height = 20
    columns = [
        "ID",
        "Private Code",
        "Description",
        "Revision Number",
    ]
    table.add_columns(*columns)
    return table


def journey_pattern_timing_link_detail_table() -> DataTable:
    """Table showing details of the selected Journey Pattern Timing Link"""
    config = TableConfig(
        name="Journey Pattern Timing Link Details",
        table_id="table-journey-pattern-timing-link-detail",
        columns=[
            "ID",
            "From Stop",
            "To Stop",
            "Route Link Ref",
            "Run Time",
            "From Wait Time",
            "Distance",
            "From Stop Atco",
            "To Stop Atco",
        ],
        min_height=3,
        height=3,
        max_height=3,
    )
    return create_data_table(config)
