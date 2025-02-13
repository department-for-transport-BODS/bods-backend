"""

fareStructureElements Parsing inside Tariff
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name
from ...models import DistanceMatrixElement, VersionedRef
from ..netex_utility import parse_versioned_ref

log = get_logger()


def parse_distance_matrix_element(elem: _Element) -> DistanceMatrixElement:
    """Parse DistanceMatrixElement element."""
    price_groups: list[VersionedRef] = []
    start_tariff_zone_ref = None
    end_tariff_zone_ref = None

    # Get id and version from attributes
    element_id = elem.get("id")
    version = elem.get("version")

    if not element_id or not version:
        raise ValueError("Missing required id or version in DistanceMatrixElement")

    for child in elem:
        tag = get_tag_name(child)
        match tag:
            case "priceGroups":
                for price_group in child:
                    if get_tag_name(price_group) == "PriceGroupRef":
                        price_groups.append(parse_versioned_ref(price_group))
            case "StartTariffZoneRef":
                start_tariff_zone_ref = parse_versioned_ref(child)
            case "EndTariffZoneRef":
                end_tariff_zone_ref = parse_versioned_ref(child)
            case _:
                log.warning("Unknown DistanceMatrixElement tag", tag=tag)
        child.clear()

    if not all([price_groups, start_tariff_zone_ref, end_tariff_zone_ref]):
        raise ValueError("Missing required fields in DistanceMatrixElement")

    return DistanceMatrixElement(
        id=element_id,
        version=version,
        priceGroups=price_groups,
        StartTariffZoneRef=start_tariff_zone_ref,
        EndTariffZoneRef=end_tariff_zone_ref,
    )
