"""
Process Flexible Service Patterns
"""

from common_layer.database.models import TransmodelServicePattern
from common_layer.xml.txc.models import TXCService
from structlog.stdlib import get_logger

from ..load.models_context import ProcessServicePatternContext, ServicePatternMapping
from .service_pattern_geom import generate_service_pattern_geometry_from_list
from .service_pattern_metadata import PatternMetadata

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


def create_flexible_service_pattern(
    service: TXCService,
    service_pattern_id: str,
    service_pattern_mapping: ServicePatternMapping,
    context: ProcessServicePatternContext,
) -> TransmodelServicePattern:
    """
    Create a single TransmodelServicePattern from a TXC flexible journey pattern

    """
    data = service_pattern_mapping.service_pattern_metadata[service_pattern_id]
    metadata = extract_flexible_pattern_metadata(service)

    # pylint: disable=R0801
    pattern = TransmodelServicePattern(
        service_pattern_id=service_pattern_id,
        description=metadata.description,
        origin=metadata.origin,
        destination=metadata.destination,
        line_name=metadata.line_name,
        revision_id=context.revision.id,
        geom=generate_service_pattern_geometry_from_list(data.stop_sequence),
    )

    log.info(
        "Created flexible service pattern",
        pattern_id=pattern.service_pattern_id,
    )
    return pattern
