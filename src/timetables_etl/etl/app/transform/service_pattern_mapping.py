"""
Creating a JourneyPattern mapping to allow for deduplication of ServicePatterns
"""

from dataclasses import dataclass, field
from typing import Sequence

from common_layer.database.models.model_naptan import NaptanStopPoint
from common_layer.xml.txc.models import (
    TXCData,
    TXCJourneyPattern,
    TXCJourneyPatternSection,
)
from structlog.stdlib import get_logger

from ..helpers.dataclasses.lookups import ReferenceDataLookups
from ..helpers.types import StopsLookup
from .utils_stops import get_pattern_stops

log = get_logger()


@dataclass
class ServicePatternMetadata:
    """Metadata about a service pattern"""

    journey_pattern_ids: list[str] = field(
        default_factory=list,
        metadata={
            "description": "list of journey pattern IDs that map to this service pattern"
        },
    )
    num_stops: int = field(
        default=0, metadata={"description": "Number of stops in this service pattern"}
    )
    stop_sequence: list[NaptanStopPoint] = field(
        default_factory=list,
        metadata={
            "description": "Ordered sequence of NaptanStopPoint objects in this service pattern"
        },
    )


@dataclass
class ServicePatternMappingStats:
    """
    Counts
    """

    service_patterns_count: int = 0
    journey_patterns_count: int = 0
    vehicle_journey_count: int = 0


@dataclass
class ServicePatternMapping:
    """Mapping between journey patterns and service patterns"""

    journey_pattern_to_service_pattern: dict[str, str] = field(
        default_factory=dict,
        metadata={"description": "Maps journey pattern ID to service pattern ID"},
    )
    vehicle_journey_to_service_pattern: dict[str, str] = field(
        default_factory=dict,
        metadata={"description": "Maps vehicle journey code to service pattern ID"},
    )
    service_pattern_metadata: dict[str, ServicePatternMetadata] = field(
        default_factory=dict,
        metadata={"description": "Metadata about each service pattern"},
    )
    stats: ServicePatternMappingStats = field(
        default_factory=ServicePatternMappingStats,
        metadata={"description": "Statistics about the mapping"},
    )


@dataclass
class ServicePatternCollections:
    """Collections of mappings related to service patterns"""

    stop_sequence_to_service_pattern: dict[tuple[str, ...], str] = field(
        default_factory=dict,
        metadata={"description": "Maps stop sequence key to service pattern ID"},
    )
    journey_pattern_to_service_pattern: dict[str, str] = field(
        default_factory=dict,
        metadata={"description": "Maps journey pattern ID to service pattern ID"},
    )
    service_pattern_to_journey_patterns: dict[str, list[str]] = field(
        default_factory=dict,
        metadata={
            "description": "Maps service pattern ID to list of journey pattern IDs"
        },
    )
    service_pattern_to_stops: dict[str, Sequence[NaptanStopPoint]] = field(
        default_factory=dict,
        metadata={"description": "Maps service pattern ID to sequence of stops"},
    )


def create_stop_sequence_key(stops: Sequence[NaptanStopPoint]) -> tuple[str, ...]:
    """
    Create a hashable key from a sequence of stops
    """
    return tuple(stop.atco_code for stop in stops)


def generate_service_pattern_id(
    service_code: str, stop_sequence_key: tuple[str, ...]
) -> str:
    """
    Generate a deterministic service pattern ID based on service code and stop sequence
    """
    return f"SP-{service_code}-{hash(stop_sequence_key) % 1000000:06d}"


def create_service_pattern_id_for_stops(
    service_code: str, stops: Sequence[NaptanStopPoint]
) -> tuple[tuple[str, ...], str]:
    """
    Create a stop sequence key and service pattern ID for a sequence of stops

    """
    stop_sequence_key = create_stop_sequence_key(stops)
    service_pattern_id = generate_service_pattern_id(service_code, stop_sequence_key)
    return stop_sequence_key, service_pattern_id


def process_journey_pattern(
    txc_jp: TXCJourneyPattern,
    jps_list: list[TXCJourneyPatternSection],
    service_code: str,
    stops_lookup: StopsLookup,
    collections: ServicePatternCollections,
) -> None:
    """
    Process a single journey pattern and update the collections
    """
    stops = get_pattern_stops(txc_jp, jps_list, stops_lookup)

    # Create a hashable representation of the stop sequence
    stop_sequence_key, service_pattern_id = create_service_pattern_id_for_stops(
        service_code, stops
    )

    # If we haven't seen this stop sequence before, create a new service pattern
    if stop_sequence_key not in collections.stop_sequence_to_service_pattern:
        collections.stop_sequence_to_service_pattern[stop_sequence_key] = (
            service_pattern_id
        )
        collections.service_pattern_to_journey_patterns[service_pattern_id] = []
        collections.service_pattern_to_stops[service_pattern_id] = stops

    # Map this journey pattern to the service pattern
    journey_pattern_id = txc_jp.id
    service_pattern_id = collections.stop_sequence_to_service_pattern[stop_sequence_key]
    collections.journey_pattern_to_service_pattern[journey_pattern_id] = (
        service_pattern_id
    )
    collections.service_pattern_to_journey_patterns[service_pattern_id].append(
        journey_pattern_id
    )


def identify_unique_patterns(
    txc: TXCData, lookups: ReferenceDataLookups
) -> ServicePatternCollections:
    """
    Identify unique stop patterns and create mappings between journey patterns and service patterns
    """
    collections = ServicePatternCollections()
    jps_list = txc.JourneyPatternSections

    for service in txc.Services:
        if service.StandardService:
            for txc_jp in service.StandardService.JourneyPattern:
                process_journey_pattern(
                    txc_jp, jps_list, service.ServiceCode, lookups.stops, collections
                )

    return collections


def resolve_vehicle_journey_patterns(
    txc: TXCData, journey_pattern_to_service_pattern: dict[str, str]
) -> dict[str, str]:
    """
    Resolve VehicleJourneyRefs (if any) to determine the service pattern for each vehicle journey

    VJs can reference other VJs which will then have the JourneyPatternRef we need
    """
    vehicle_journey_to_service_pattern: dict[str, str] = {}

    # First pass - map all vehicle journeys that directly reference a journey pattern
    vehicle_journey_code_to_service_pattern: dict[str, str] = {}

    for vj in txc.VehicleJourneys:
        if vj.VehicleJourneyCode is None:
            continue
        if vj.JourneyPatternRef:
            jp_id = vj.JourneyPatternRef
            if jp_id in journey_pattern_to_service_pattern:
                service_pattern_id = journey_pattern_to_service_pattern[jp_id]
                vehicle_journey_to_service_pattern[vj.VehicleJourneyCode] = (
                    service_pattern_id
                )

                if vj.VehicleJourneyCode:
                    vehicle_journey_code_to_service_pattern[vj.VehicleJourneyCode] = (
                        service_pattern_id
                    )
            else:
                log.warning(
                    "Journey pattern not found for vehicle journey.",
                    journey_pattern_id=jp_id,
                    vehicle_journey_id=vj.VehicleJourneyCode,
                )

    # Second pass - resolve vehicle journeys that reference other vehicle journeys
    for vj in txc.VehicleJourneys:
        if vj.VehicleJourneyCode is None:
            continue

        if (
            vj.VehicleJourneyCode not in vehicle_journey_to_service_pattern
            and vj.VehicleJourneyRef
        ):
            referenced_vj_code = vj.VehicleJourneyRef

            if referenced_vj_code in vehicle_journey_code_to_service_pattern:
                vehicle_journey_to_service_pattern[vj.VehicleJourneyCode] = (
                    vehicle_journey_code_to_service_pattern[referenced_vj_code]
                )
            else:
                log.warning(
                    "Could not resolve vehicle journey reference.",
                    referenced_vehicle_journey_code=referenced_vj_code,
                    vehicle_journey_id=vj.VehicleJourneyCode,
                )

    return vehicle_journey_to_service_pattern


def create_service_pattern_metadata(
    service_pattern_to_journey_patterns: dict[str, list[str]],
    service_pattern_to_stops: dict[str, Sequence[NaptanStopPoint]],
) -> dict[str, ServicePatternMetadata]:
    """
    Create metadata about each service pattern
    """
    service_pattern_metadata: dict[str, ServicePatternMetadata] = {}

    for sp_id, jp_ids in service_pattern_to_journey_patterns.items():
        # Get the NaptanStopPoint objects for this service pattern
        stops = service_pattern_to_stops.get(sp_id, [])

        # Create the metadata with the actual NaptanStopPoint objects
        service_pattern_metadata[sp_id] = ServicePatternMetadata(
            journey_pattern_ids=jp_ids, num_stops=len(stops), stop_sequence=list(stops)
        )

    return service_pattern_metadata


def map_unique_journey_patterns(
    txc: TXCData, lookups: ReferenceDataLookups
) -> ServicePatternMapping:
    """
    Map journey patterns to deduplicated service patterns based on unique stop sequences.

    - Identify the unique pattern of stops
    - Map Vehicle Journeys to Journey Patterns
    - Create Mappings
    """
    collections = identify_unique_patterns(txc, lookups)

    vehicle_journey_to_service_pattern = resolve_vehicle_journey_patterns(
        txc, collections.journey_pattern_to_service_pattern
    )

    service_pattern_metadata = create_service_pattern_metadata(
        collections.service_pattern_to_journey_patterns,
        collections.service_pattern_to_stops,
    )

    log.info(
        "Created unique service patterns from journey patterns.",
        unique_service_pattern_count=len(collections.stop_sequence_to_service_pattern),
        journey_pattern_count=len(collections.journey_pattern_to_service_pattern),
        vehicle_journey_count=len(vehicle_journey_to_service_pattern),
    )

    stats = ServicePatternMappingStats(
        service_patterns_count=len(collections.stop_sequence_to_service_pattern),
        journey_patterns_count=len(collections.journey_pattern_to_service_pattern),
        vehicle_journey_count=len(vehicle_journey_to_service_pattern),
    )

    return ServicePatternMapping(
        journey_pattern_to_service_pattern=collections.journey_pattern_to_service_pattern,
        vehicle_journey_to_service_pattern=vehicle_journey_to_service_pattern,
        service_pattern_metadata=service_pattern_metadata,
        stats=stats,
    )
