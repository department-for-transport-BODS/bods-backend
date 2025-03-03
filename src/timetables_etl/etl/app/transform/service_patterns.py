"""
Make Transmodel Service Patterns
"""

from common_layer.database.models import TransmodelServicePattern
from structlog.stdlib import get_logger

from ..load.models_context import ProcessServicePatternContext
from ..transform.service_pattern_metadata import make_metadata
from .service_pattern_geom import generate_service_pattern_geometry_from_list
from .service_pattern_mapping import ServicePatternMapping

log = get_logger()


def create_service_pattern(
    service_pattern_id: str,
    service_pattern_mapping: ServicePatternMapping,
    context: ProcessServicePatternContext,
) -> TransmodelServicePattern:
    """
    Create a single TransmodelServicePattern from a TXC journey pattern
    """

    data = service_pattern_mapping.service_pattern_metadata[service_pattern_id]
    metadata = make_metadata(data, service_pattern_mapping.line_to_txc_line)

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
        "Created service pattern",
        pattern_id=pattern.service_pattern_id,
    )
    return pattern
