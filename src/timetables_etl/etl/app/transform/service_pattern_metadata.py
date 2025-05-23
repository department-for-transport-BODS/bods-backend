"""
Meta Data Extraction
"""

from dataclasses import dataclass

from common_layer.database.models import NaptanStopPoint
from common_layer.xml.txc.models import (
    TXCJourneyPattern,
    TXCJourneyPatternSection,
    TXCLine,
    TXCService,
)
from structlog.stdlib import get_logger

from ..helpers import StopsLookup
from ..transform.utils_stops import get_first_last_stops
from .service_pattern_mapping import ServicePatternMetadata

log = get_logger()


@dataclass(frozen=True)
class LineDescription:
    """Wrapper for line description data"""

    origin: str | None
    destination: str | None
    description: str


@dataclass(frozen=True)
class PatternMetadata:
    """Metadata about a service pattern's origin and destination"""

    origin: str
    destination: str
    description: str
    line_name: str

    @classmethod
    def unknown(cls, line_name: str) -> "PatternMetadata":
        """Create a metadata object for unknown origin/destination"""
        return cls(
            origin="unknown",
            destination="unknown",
            description="unknown",
            line_name=line_name,
        )


def get_first_and_last_stops(
    stop_sequence: list[NaptanStopPoint],
) -> tuple[NaptanStopPoint | None, NaptanStopPoint | None]:
    """
    Safely get the first and last stops from a sequence.

    """
    if not stop_sequence:
        return None, None

    first_stop = stop_sequence[0]
    last_stop = stop_sequence[-1]

    return first_stop, last_stop


def get_origin_destination(
    service: TXCService, sp_data: ServicePatternMetadata
) -> tuple[str, str]:
    """
    Get the origin and destination strings for the given service
    """
    first_stop, last_stop = get_first_and_last_stops(sp_data.stop_sequence)
    if first_stop and last_stop:
        return first_stop.common_name, last_stop.common_name

    if service.StandardService:
        return service.StandardService.Origin, service.StandardService.Destination

    if service.FlexibleService:
        return service.FlexibleService.Origin, service.FlexibleService.Destination

    return "unknown", "unknown"


def get_description(
    line: TXCLine,
    sp_data: ServicePatternMetadata,
    service_origin: str,
    service_destination: str,
) -> str:
    """
    Get the description for the service using the given line
    """

    # Try to get description from the line
    if (
        sp_data.direction in ["inbound", "antiClockwise"]
        and line.InboundDescription
        and line.InboundDescription.Description
    ):
        return line.InboundDescription.Description

    if (
        sp_data.direction in ["outbound", "clockwise"]
        and line.OutboundDescription
        and line.OutboundDescription.Description
    ):
        return line.OutboundDescription.Description

    if sp_data.direction not in ["inbound", "outbound"]:
        log.warning(
            "Unexpected direction value for service pattern",
            line_id=sp_data.line_id,
            direction=sp_data.direction,
            journey_pattern_ids=sp_data.journey_pattern_ids,
        )

    # Fallback if we're unable to get the description from the line data
    if service_origin != "unknown" and service_destination != "unknown":
        return f"{service_origin} - {service_destination}"

    return "unknown"


def make_metadata(
    service: TXCService,
    sp_data: ServicePatternMetadata,
    line_to_txc_line: dict[str, TXCLine],
):
    """
    Generate the metadata
    """
    origin, destination = get_origin_destination(service, sp_data)
    line_name = "unknown"
    description = "unknown"

    line = line_to_txc_line.get(sp_data.line_id)
    if line:
        line_name = line.LineName
        description = get_description(line, sp_data, origin, destination)

    return PatternMetadata(
        origin=origin,
        destination=destination,
        description=description,
        line_name=line_name,
    )


def get_line_description(line: TXCLine, direction: str) -> LineDescription | None:
    """
    Extract relevant direction description from line
    """
    description = (
        line.InboundDescription if direction == "inbound" else line.OutboundDescription
    )
    if not description:
        return None
    return LineDescription(
        origin=description.Origin,
        destination=description.Destination,
        description=description.Description,
    )


def extract_pattern_metadata(
    service: TXCService,
    jp: TXCJourneyPattern,
    journey_pattern_sections: list[TXCJourneyPatternSection],
    stop_mapping: StopsLookup,
) -> PatternMetadata:
    """
    Extract pattern metadata with priority:
    1. Line description data if available
    2. First/last stop names with generated description
    3. Unknown pattern as fallback
    """
    first_stop, last_stop = get_first_last_stops(
        jp, journey_pattern_sections, stop_mapping
    )

    if not service.Lines:
        log.warning("No Lines in TXC Service")
        return PatternMetadata(
            origin=first_stop,
            destination=last_stop,
            description=f"{first_stop} - {last_stop}",
            line_name="unknown",
        )

    line = service.Lines[0]
    if len(service.Lines) > 1:
        log.warning("More than 1 Line using first for Service Patterns")

    line_desc = get_line_description(line, jp.Direction)

    if line_desc and line_desc.origin and line_desc.destination:
        return PatternMetadata(
            origin=line_desc.origin,
            destination=line_desc.destination,
            description=line_desc.description,
            line_name=line.LineName,
        )

    if not first_stop and not last_stop:
        return PatternMetadata.unknown(line.LineName)

    return PatternMetadata(
        origin=first_stop,
        destination=last_stop,
        description=f"{first_stop} - {last_stop}",
        line_name=line.LineName,
    )
