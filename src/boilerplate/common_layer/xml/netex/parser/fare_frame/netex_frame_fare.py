"""
FareFrame
"""

from dataclasses import dataclass

from common_layer.xml.netex.models.fare_frame.netex_frame_defaults import (
    FrameDefaultsStructure,
)
from common_layer.xml.netex.models.fare_frame.netex_frame_fare import (
    PricingParameterSet,
)
from common_layer.xml.netex.models.fare_frame.netex_sales_offer_package import (
    SalesOfferPackage,
)
from common_layer.xml.netex.parser.fare_frame.netex_fare_sales_offer_package import (
    parse_sales_offer_packages,
)
from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name
from ...models import FareFrame
from ...models.fare_frame import FareTable, Tariff
from ...models.fare_frame.netex_fare_preassigned import PreassignedFareProduct
from ...models.fare_frame.netex_fare_zone import FareZone
from ...models.netex_utility import MultilingualString, VersionedRef
from ...parser.fare_frame.netex_fare_table import parse_fare_tables
from ..data_objects.netex_frame_defaults import parse_frame_defaults
from ..netex_utility import (
    get_netex_text,
    parse_multilingual_string,
    parse_versioned_ref,
)
from .netex_fare_preassigned_fare_product import parse_preassigned_fare_products
from .netex_fare_tariff import parse_tariffs
from .netex_fare_zone import parse_fare_zones
from .netex_pricing_parameter_set import parse_pricing_parameter_set

log = get_logger()


def parse_fare_frame_attributes(elem: _Element) -> tuple[str, str, str | None]:
    """Parse required FareFrame attributes"""
    frame_id = elem.get("id")
    version = elem.get("version")
    responsibility_set_ref = elem.get("responsibilitySetRef")

    if not frame_id or not version:
        raise ValueError("Missing required attributes in FareFrame")

    return frame_id, version, responsibility_set_ref


@dataclass
class FareFrameCoreAttributes:
    """
    Top Level Attribuutes
    """

    name: MultilingualString | None
    description: MultilingualString | None
    type_of_frame_ref: VersionedRef | None
    data_source_ref: str | None


@dataclass
class FareFrameContent:
    """
    Complex Context
    """

    frame_defaults: FrameDefaultsStructure | None
    pricing_parameter_set: PricingParameterSet | None
    fare_tables: list[FareTable]
    fare_products: list[PreassignedFareProduct]
    tariffs: list[Tariff]
    fare_zones: list[FareZone]
    sales_offer_packages: list[SalesOfferPackage]


def parse_fare_frame_core_attributes(elem: _Element) -> FareFrameCoreAttributes:
    """Parse optional core FareFrame attributes"""
    return FareFrameCoreAttributes(
        name=parse_multilingual_string(elem, "Name"),
        description=parse_multilingual_string(elem, "Description"),
        type_of_frame_ref=parse_versioned_ref(elem, "TypeOfFrameRef"),
        data_source_ref=get_netex_text(elem, "dataSourceRef"),
    )


def parse_fare_frame_content(elem: _Element) -> FareFrameContent:
    """Parse FareFrame content elements"""
    content = FareFrameContent(
        frame_defaults=None,
        pricing_parameter_set=None,
        fare_tables=[],
        fare_products=[],
        tariffs=[],
        fare_zones=[],
        sales_offer_packages=[],
    )

    for child in elem:
        tag = get_tag_name(child)
        match tag:
            case "FrameDefaults":
                content.frame_defaults = parse_frame_defaults(child)
            case "PricingParameterSet":
                content.pricing_parameter_set = parse_pricing_parameter_set(child)
            case "fareTables":
                content.fare_tables = parse_fare_tables(child)
            case "fareProducts":
                content.fare_products = parse_preassigned_fare_products(child)
            case "tariffs":
                content.tariffs = parse_tariffs(child)
            case "fareZones":
                content.fare_zones = parse_fare_zones(child)
            case "salesOfferPackages":
                content.sales_offer_packages = parse_sales_offer_packages(child)
            case "Name" | "Description" | "TypeOfFrameRef" | "dataSourceRef":
                pass  # These are handled in core attributes
            case _:
                log.warning("Unknown FareFrame tag", tag=tag)
        child.clear()

    return content


def parse_fare_frame(elem: _Element) -> FareFrame:
    """Parse FareFrame element"""
    frame_id, version, responsibility_set_ref = parse_fare_frame_attributes(elem)
    core_attrs = parse_fare_frame_core_attributes(elem)
    content = parse_fare_frame_content(elem)

    return FareFrame(
        id=frame_id,
        version=version,
        responsibilitySetRef=responsibility_set_ref,
        Name=core_attrs.name,
        Description=core_attrs.description,
        TypeOfFrameRef=core_attrs.type_of_frame_ref,
        dataSourceRef=core_attrs.data_source_ref,
        FrameDefaults=content.frame_defaults,
        PricingParameterSet=content.pricing_parameter_set,
        fareZones=content.fare_zones if content.fare_zones else None,
        tariffs=content.tariffs if content.tariffs else None,
        fareProducts=content.fare_products if content.fare_products else None,
        fareTables=content.fare_tables if content.fare_tables else None,
        geographicalUnits=None,
        usageParameters=None,
        distributionChannels=None,
        fulfilmentMethods=None,
        typesOfTravelDocuments=None,
        priceGroups=None,
        salesOfferPackages=(
            content.sales_offer_packages if content.sales_offer_packages else None
        ),
    )
