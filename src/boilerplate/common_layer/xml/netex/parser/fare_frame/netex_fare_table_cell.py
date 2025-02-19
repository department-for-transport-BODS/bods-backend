"""
FareTable Cell Parsing
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...models.fare_frame.netex_fare_table import Cell, DistanceMatrixElementPrice
from ..netex_utility import get_netex_element, parse_versioned_ref

log = get_logger()


def parse_distance_matrix_element_price(
    elem: _Element,
) -> DistanceMatrixElementPrice | None:
    """
    Parse a single DistanceMatrixElementPrice element
    """
    price_id = elem.get("id")
    price_version = elem.get("version")

    if not price_id or not price_version:
        log.warning("DistanceMatrixElementPrice missing required fields")
        return None

    return DistanceMatrixElementPrice(
        id=price_id,
        version=price_version,
        GeographicalIntervalPriceRef=parse_versioned_ref(
            elem, "GeographicalIntervalPriceRef"
        ),
        DistanceMatrixElementRef=parse_versioned_ref(elem, "DistanceMatrixElementRef"),
    )


def parse_cell(elem: _Element) -> Cell | None:
    """
    Parse a single Cell element
    """
    cell_id = elem.get("id")
    cell_version = elem.get("version")
    cell_order = elem.get("order")

    if not cell_id or not cell_version or not cell_order:
        log.warning("Cell missing required fields")
        return None

    # Parse price element
    price_elem = get_netex_element(elem, "DistanceMatrixElementPrice")
    if price_elem is None:
        log.warning("Cell missing DistanceMatrixElementPrice")
        return None

    price = parse_distance_matrix_element_price(price_elem)
    if not price:
        return None

    return Cell(
        id=cell_id,
        version=cell_version,
        order=cell_order,
        DistanceMatrixElementPrice=price,
        ColumnRef=parse_versioned_ref(elem, "ColumnRef"),
        RowRef=parse_versioned_ref(elem, "RowRef"),
    )
