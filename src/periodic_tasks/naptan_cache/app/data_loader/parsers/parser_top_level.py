"""
Non Nested Top Level Tags Parsing of a StopPoint
"""

from lxml import etree

from .xml_constants import NAPTAN_NS_PREFIX

TOP_LEVEL_TAGS = {
    f"{NAPTAN_NS_PREFIX}AtcoCode": "AtcoCode",
    f"{NAPTAN_NS_PREFIX}NaptanCode": "NaptanCode",
    f"{NAPTAN_NS_PREFIX}LocalityName": "LocalityName",
    f"{NAPTAN_NS_PREFIX}StopType": "StopType",
    f"{NAPTAN_NS_PREFIX}NptgLocalityRef": "NptgLocalityRef",
    f"{NAPTAN_NS_PREFIX}AdministrativeAreaRef": "AdministrativeAreaRef",
}


def parse_top_level(
    stop_point: etree._Element,
) -> tuple[dict[str, str | None], bool]:
    """
    Parse basic fields from stop point XML with minimal traversal
    Returns a tuple of (field_data, atco_found)
    """
    result: dict[str, str | None] = {
        "AtcoCode": None,
        "NaptanCode": None,
        "LocalityName": None,
        "StopType": None,
        "NptgLocalityRef": None,
        "AdministrativeAreaRef": None,
    }

    atco_found = False

    for child in stop_point:
        if child.tag in TOP_LEVEL_TAGS:
            value = child.text or None
            field_name = TOP_LEVEL_TAGS[child.tag]
            result[field_name] = value
            if field_name == "AtcoCode" and value is not None:
                atco_found = True

    return result, atco_found
