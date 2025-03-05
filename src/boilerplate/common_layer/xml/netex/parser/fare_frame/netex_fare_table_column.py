"""
FareTable Columns Parsing
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name
from ...models.fare_frame.netex_fare_table import FareTableColumn
from ..netex_references import parse_object_references
from ..netex_utility import get_netex_element, parse_multilingual_string

log = get_logger()


def parse_fare_table_column(elem: _Element) -> FareTableColumn | None:
    """
    Parse a single FareTableColumn element
    """
    column_id = elem.get("id")
    column_version = elem.get("version")
    column_order = elem.get("order")
    name = parse_multilingual_string(elem, "Name")

    if not column_id or not column_version or not column_order or not name:
        log.warning("FareTableColumn missing required fields")
        return None

    representing = None
    representing_elem = get_netex_element(elem, "representing")
    if representing_elem is not None:
        representing = parse_object_references(representing_elem)
    return FareTableColumn(
        id=column_id,
        version=column_version,
        order=column_order,
        Name=name,
        representing=representing,
    )


def parse_fare_table_columns(elem: _Element) -> list[FareTableColumn]:
    """
    Parse columns from a FareTable element
    """
    columns: list[FareTableColumn] = []
    columns_elem = get_netex_element(elem, "columns")
    if columns_elem is not None:
        for column_elem in columns_elem:
            if get_tag_name(column_elem) == "Column":
                column = parse_fare_table_column(column_elem)
                if column:
                    columns.append(column)
    return columns
