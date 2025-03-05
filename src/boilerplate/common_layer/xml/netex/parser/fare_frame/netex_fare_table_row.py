"""
Fare Table Rows
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name
from ...models.fare_frame.netex_fare_table import FareTableRow
from ..netex_utility import get_netex_element, parse_multilingual_string

log = get_logger()


def parse_fare_table_row(elem: _Element) -> FareTableRow | None:
    """
    Parse a single FareTableRow element
    """
    row_id = elem.get("id")
    row_version = elem.get("version")
    row_order = elem.get("order")
    name = parse_multilingual_string(elem, "Name")

    if not row_id or not row_version or not row_order or not name:
        log.warning("FareTableRow missing required fields")
        return None

    return FareTableRow(id=row_id, version=row_version, order=row_order, Name=name)


def parse_fare_table_rows(elem: _Element) -> list[FareTableRow]:
    """
    Parse rows from a FareTable element
    """
    rows: list[FareTableRow] = []
    rows_elem = get_netex_element(elem, "rows")
    if rows_elem is not None:
        for row_elem in rows_elem:
            if get_tag_name(row_elem) == "Row":
                row = parse_fare_table_row(row_elem)
                if row:
                    rows.append(row)
    return rows
