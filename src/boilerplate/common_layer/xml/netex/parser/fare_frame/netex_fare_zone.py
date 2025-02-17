"""
FareZone Parsing
"""

from lxml.etree import _Element
from structlog.stdlib import get_logger

from ....utils import get_tag_name
from ...models import PointRefs
from ...models.fare_frame.netex_fare_zone import FareZone
from ..netex_references import parse_point_refs
from ..netex_utility import get_netex_element, parse_multilingual_string

log = get_logger()


def parse_fare_zone(elem: _Element) -> FareZone | None:
    """
    Parse a single FareZone element
    """
    zone_id = elem.get("id")
    zone_version = elem.get("version")
    name = parse_multilingual_string(elem, "Name")

    if not zone_id or not zone_version or not name:
        log.warning(
            "FareZone missing required fields",
            id=zone_id,
            version=zone_version,
            name=name,
        )
        return None

    members: PointRefs | None = None
    members_elem = get_netex_element(elem, "members")
    if members_elem is not None:
        members = parse_point_refs(members_elem)

    return FareZone(id=zone_id, version=zone_version, Name=name, members=members)


def parse_fare_zones(elem: _Element) -> list[FareZone]:
    """
    Parse a list of FareZone elements
    """
    zones: list[FareZone] = []
    for child in elem:
        if get_tag_name(child) == "FareZone":
            zone = parse_fare_zone(child)
            if zone:
                zones.append(zone)
    return zones
