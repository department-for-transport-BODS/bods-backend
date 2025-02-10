"""
Meta Data Extraction
"""

from dataclasses import dataclass
from uuid import uuid4

from common_layer.xml.txc.models import (
    TXCFlexibleJourneyPattern,
    TXCJourneyPattern,
    TXCJourneyPatternSection,
    TXCLine,
    TXCService,
)
from structlog.stdlib import get_logger

from ..helpers import StopsLookup
from ..transform.utils_stops import get_first_last_stops

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


def make_service_pattern_id(
    service: TXCService, jp: TXCJourneyPattern | TXCFlexibleJourneyPattern
):
    """
    Generate a Unique Service Pattern ID to be used
    """
    return f"{service.ServiceCode}-{jp.id}-{uuid4()}"
