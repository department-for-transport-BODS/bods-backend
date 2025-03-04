"""
Fare Table Parsing
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name
from ...models import VersionedRef
from ...models.fare_frame.netex_fare_table import FareTable
from ..netex_references import parse_pricable_object_refs
from ..netex_utility import (
    get_netex_element,
    parse_multilingual_string,
    parse_versioned_ref,
)
from .netex_fare_table_column import parse_fare_table_columns
from .netex_fare_table_row import parse_fare_table_rows

log = get_logger()


def parse_used_in(elem: _Element) -> dict[str, VersionedRef]:
    """
    Parse usedIn references from a FareTable element
    """
    used_in: dict[str, VersionedRef] = {}
    used_in_elem = get_netex_element(elem, "usedIn")
    if used_in_elem is not None:
        for ref_elem in used_in_elem:
            ref = parse_versioned_ref(ref_elem, "")
            if ref:
                tag_name = get_tag_name(ref_elem)
                if tag_name:
                    used_in[tag_name] = ref
    return used_in


def parse_specifics(elem: _Element) -> dict[str, VersionedRef]:
    """
    Parse specifics references from a FareTable element
    """
    specifics: dict[str, VersionedRef] = {}
    specifics_elem = get_netex_element(elem, "specifics")
    if specifics_elem is not None:
        for ref_elem in specifics_elem:
            ref = parse_versioned_ref(ref_elem, "")
            if ref:
                tag_name = get_tag_name(ref_elem)
                if tag_name:
                    specifics[tag_name] = ref
    return specifics


def parse_fare_table(elem: _Element) -> FareTable | None:
    """
    Parse a single FareTable element
    """
    table_id = elem.get("id")
    table_version = elem.get("version")
    name = parse_multilingual_string(elem, "Name")
    description = parse_multilingual_string(elem, "Description")

    if not table_id or not table_version or not name:
        log.warning("FareTable missing required fields")
        return None

    nested_tables_elements = get_netex_element(elem, "includes")

    includes: list[FareTable] = []
    if nested_tables_elements is not None:
        for nested_table in nested_tables_elements:
            parsed_nested_table = parse_fare_table(nested_table)
            if parsed_nested_table is not None:
                includes.append(parsed_nested_table)
    return FareTable(
        id=table_id,
        version=table_version,
        Name=name,
        Description=description,
        pricesFor=parse_pricable_object_refs(elem),
        usedIn=parse_used_in(elem),
        specifics=parse_specifics(elem),
        columns=parse_fare_table_columns(elem),
        rows=parse_fare_table_rows(elem),
        includes=includes,
    )


def parse_fare_tables(elem: _Element) -> list[FareTable]:
    """Parse fareTables list element"""
    fare_tables: list[FareTable] = []
    for fare_table in elem:
        if get_tag_name(fare_table) == "FareTable":
            fare_table = parse_fare_table(fare_table)
            if fare_table is not None:

                fare_tables.append(fare_table)
        else:
            log.warning("Unknown fareTables tag", tag=get_tag_name(fare_table))
    return fare_tables
