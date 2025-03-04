"""
Object References
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...utils import get_tag_name
from ..models import (
    ObjectReferences,
    PointRefs,
    PricableObjectRefs,
    ScheduledStopPointReference,
)
from .netex_scheduled_stop_point_ref import parse_scheduled_stop_point_ref
from .netex_utility import VersionedRef, parse_versioned_ref

log = get_logger()


def parse_object_references(elem: _Element) -> ObjectReferences:
    """
    Parse objectReferences element."
    """

    return ObjectReferences(
        OperatorRef=parse_versioned_ref(elem, "OperatorRef"),
        LineRef=parse_versioned_ref(elem, "LineRef"),
        FareZoneRef=parse_versioned_ref(elem, "FareZoneRef"),
    )


def parse_pricable_object_refs(elem: _Element) -> PricableObjectRefs:
    """
    Parse pricesFor
    pointRefs_RelStructure
    """
    return PricableObjectRefs(
        PreassignedFareProductRef=parse_versioned_ref(
            elem, "PreassignedFareProductRef"
        ),
        SalesOfferPackageRef=parse_versioned_ref(elem, "SalesOfferPackageRef"),
        UserProfileRef=parse_versioned_ref(elem, "UserProfileRef"),
    )


def parse_point_refs(elem: _Element) -> PointRefs:
    """
    Parser for pointRefs_RelStructure.
    """
    scheduled_stop_points: list[ScheduledStopPointReference] = []
    timing_points: list[VersionedRef] = []
    route_points: list[VersionedRef] = []
    fare_points: list[VersionedRef] = []
    generic_points: list[VersionedRef] = []

    for child in elem:
        ref = child.get("ref")
        if ref is None:
            continue

        version = child.get("version")
        tag_name = get_tag_name(child)

        if tag_name is None:
            continue

        match tag_name:
            case "ScheduledStopPointRef":
                stop_ref = parse_scheduled_stop_point_ref(child)
                if stop_ref is not None:
                    scheduled_stop_points.append(stop_ref)

            case "TimingPointRef":
                timing_points.append(VersionedRef(ref=ref, version=version))

            case "RoutePointRef":
                route_points.append(VersionedRef(ref=ref, version=version))

            case "FareScheduledStopPointRef":
                fare_points.append(VersionedRef(ref=ref, version=version))

            case "PointRef":
                generic_points.append(VersionedRef(ref=ref, version=version))

            case _:
                continue

    return PointRefs(
        ScheduledStopPointRef=scheduled_stop_points,
        TimingPointRef=timing_points,
        RoutePointRef=route_points,
        FareScheduledStopPointRef=fare_points,
        PointRef=generic_points,
    )
