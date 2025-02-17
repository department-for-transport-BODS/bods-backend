"""
Process Flexible Service Patterns
"""

from typing import Sequence

from common_layer.database.models import (
    OrganisationDatasetRevision,
    TransmodelServicePattern,
)
from common_layer.xml.txc.helpers.service import extract_flexible_pattern_stop_refs
from common_layer.xml.txc.models import TXCFlexibleJourneyPattern, TXCService
from etl.app.helpers.dataclasses.stop_points import NonExistentNaptanStop
from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape
from shapely import LineString, Point
from structlog.stdlib import get_logger

from ..helpers.types import StopsLookup
from .service_pattern_metadata import PatternMetadata, make_service_pattern_id

log = get_logger()


def extract_flexible_pattern_metadata(
    service: TXCService,
) -> PatternMetadata:
    """
    Extract pattern metadata from a flexible service
    """
    if not service.FlexibleService:
        raise ValueError("Service must have FlexibleService data")

    return PatternMetadata(
        origin=service.FlexibleService.Origin,
        destination=service.FlexibleService.Destination,
        description=f"{service.FlexibleService.Origin} - {service.FlexibleService.Destination}",
        line_name=service.Lines[0].LineName if service.Lines else "unknown",
    )


def generate_flexible_pattern_geometry(
    stops: Sequence[str],
    stop_mapping: StopsLookup,
) -> WKBElement | None:
    """
    Generate geometry for a flexible service pattern.
    Returns None if insufficient points available to create a LineString.

    Returns:
        WKBElement containing LineString geometry if 2+ points available,
        None otherwise
    """
    route_points: list[Point] = []
    for stop in stops:
        stop_data = stop_mapping[stop]
        if not isinstance(stop_data, NonExistentNaptanStop):
            route_points.append(stop_data.shape)

    if len(route_points) < 2:
        log.warning(
            "Fewer than 2 stops so a Postgres LineString cannot be created, returning None",
            stops=stops,
        )
        return None

    return from_shape(LineString(route_points), srid=4326)


def create_flexible_service_pattern(
    service: TXCService,
    jp: TXCFlexibleJourneyPattern,
    revision: OrganisationDatasetRevision,
    stop_mapping: StopsLookup,
) -> TransmodelServicePattern:
    """
    Create a single TransmodelServicePattern from a TXC flexible journey pattern

    """
    log.info(
        "Processing Flexible Service Pattern",
        service_code=service.ServiceCode,
        journey_pattern_id=jp.id,
    )
    metadata = extract_flexible_pattern_metadata(service)
    log.debug("Flexible Metadata extracted", metadata=metadata)
    stops = extract_flexible_pattern_stop_refs(jp)
    log.debug("Stop sequence found", stops=stops)
    geom = generate_flexible_pattern_geometry(stops, stop_mapping)
    log.debug("Geometry created", geom=geom)
    pattern = TransmodelServicePattern(
        service_pattern_id=make_service_pattern_id(service, jp),
        origin=metadata.origin,
        destination=metadata.destination,
        description=metadata.description,
        revision_id=revision.id,
        line_name=metadata.line_name,
        geom=geom,
    )

    log.info(
        "Created flexible service pattern",
        pattern_id=pattern.service_pattern_id,
    )
    return pattern
