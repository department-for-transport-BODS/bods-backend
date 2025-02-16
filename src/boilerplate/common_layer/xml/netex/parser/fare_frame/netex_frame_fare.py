"""
FareFrame
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name
from ...models import FareFrame
from ...models.fare_frame.netex_fare_preassigned import (
    ConditionSummary,
    PreassignedFareProduct,
)
from ..netex_utility import (
    get_netex_element,
    get_netex_text,
    parse_multilingual_string,
    parse_versioned_ref,
)
from .netex_fare_tariff import parse_tariff
from .netex_fare_zone import parse_fare_zones

log = get_logger()


def parse_preassigned_fare_product(elem: _Element) -> PreassignedFareProduct | None:
    """
    Parse a single PreassignedFareProduct element
    """
    product_id = elem.get("id")
    product_version = elem.get("version")
    name = parse_multilingual_string(elem, "Name")

    if not product_id or not product_version or not name:
        log.warning("PreassignedFareProduct missing required fields")
        return None

    charging_moment_ref = parse_versioned_ref(elem, "ChargingMomentRef")
    charging_moment_type = get_netex_text(elem, "ChargingMomentType")
    type_of_fare_product_ref = parse_versioned_ref(elem, "TypeOfFareProductRef")
    operator_ref = parse_versioned_ref(elem, "OperatorRef")

    # Parse ConditionSummary
    condition_summary_elem = get_netex_element(elem, "ConditionSummary")
    condition_summary = None
    if condition_summary_elem is not None:
        condition_summary = ConditionSummary(
            FareStructureType=get_netex_text(
                condition_summary_elem, "FareStructureType"
            ),
            TariffBasis=get_netex_text(condition_summary_elem, "TariffBasis"),
            IsPersonal=get_netex_text(condition_summary_elem, "IsPersonal") == "true",
        )

    return PreassignedFareProduct(
        id=product_id,
        version=product_version,
        Name=name,
        ChargingMomentRef=charging_moment_ref,
        ChargingMomentType=charging_moment_type,
        TypeOfFareProductRef=type_of_fare_product_ref,
        OperatorRef=operator_ref,
        ConditionSummary=condition_summary,
        validableElements=[],  # Parse validable elements
        accessRightsInProduct=[],  # Parse access rights
        ProductType=get_netex_text(elem, "ProductType"),
    )


def parse_fare_frame(elem: _Element) -> FareFrame:
    """
    Parse a FareFrame containing fare-related definitions
    """
    # Parse required attributes
    frame_id = elem.get("id")
    if frame_id is None:
        raise ValueError("Missing Frame ID")

    version = elem.get("version")
    if version is None:
        raise ValueError("Missing Version")

    responsibility_set_ref = elem.get("responsibilitySetRef")
    if responsibility_set_ref is None:
        raise ValueError("Missing ResponsibilitySetRef")

    # Parse optional core attributes
    name = parse_multilingual_string(elem, "Name")
    description = parse_multilingual_string(elem, "Description")
    type_of_frame_ref = parse_versioned_ref(elem, "TypeOfFrameRef")
    data_source_ref = elem.get("dataSourceRef")

    # Parse optional components
    fare_zones = []
    fare_zones_elem = get_netex_element(elem, "fareZones")
    if fare_zones_elem is not None:
        fare_zones = parse_fare_zones(fare_zones_elem)

    tariffs = []
    tariffs_elem = get_netex_element(elem, "tariffs")
    if tariffs_elem is not None:
        for child in tariffs_elem:
            if get_tag_name(child) == "Tariff":
                tariff = parse_tariff(child)
                if tariff:
                    tariffs.append(tariff)

    return FareFrame(
        id=frame_id,
        version=version,
        responsibilitySetRef=responsibility_set_ref,
        Name=name,
        Description=description,
        TypeOfFrameRef=type_of_frame_ref,
        dataSourceRef=data_source_ref,
        fareZones=fare_zones if fare_zones else None,
        tariffs=tariffs if tariffs else None,
        # Add other optional components as needed
    )
