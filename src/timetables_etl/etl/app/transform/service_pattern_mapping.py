"""
Creating a JourneyPattern mapping to allow for deduplication of ServicePatterns
"""

from typing import Sequence

from common_layer.database.models.model_naptan import NaptanStopPoint
from common_layer.xml.txc.models import TXCData
from pydantic import BaseModel, Field
from structlog.stdlib import get_logger

from ..helpers.dataclasses.lookups import ReferenceDataLookups
from .utils_stops import get_pattern_stops

log = get_logger()


class ServicePatternMetadata(BaseModel):
    """Metadata about a service pattern"""

    journey_pattern_ids: list[str] = Field(
        description="List of journey pattern IDs that map to this service pattern"
    )
    num_stops: int = Field(description="Number of stops in this service pattern")


class ServicePatternMapping(BaseModel):
    """Mapping between journey patterns and service patterns"""

    journey_pattern_to_service_pattern: dict[str, str] = Field(
        description="Maps journey pattern ID to service pattern ID"
    )
    vehicle_journey_to_service_pattern: dict[str, str] = Field(
        description="Maps vehicle journey code to service pattern ID"
    )
    service_pattern_metadata: dict[str, ServicePatternMetadata] = Field(
        description="Metadata about each service pattern"
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


def identify_unique_patterns(txc: TXCData, lookups: ReferenceDataLookups) -> tuple[
    dict[tuple[str, ...], str],  # stop_sequence_to_service_pattern
    dict[str, str],  # journey_pattern_to_service_pattern
    dict[str, list[str]],  # service_pattern_to_journey_patterns
]:
    """
    Identify unique stop patterns and create mappings between
    journey patterns and service patterns
    """
    stop_sequence_to_service_pattern: dict[tuple[str, ...], str] = {}
    journey_pattern_to_service_pattern: dict[str, str] = {}
    service_pattern_to_journey_patterns: dict[str, list[str]] = {}

    jps_list = txc.JourneyPatternSections

    for service in txc.Services:
        if service.StandardService:
            for txc_jp in service.StandardService.JourneyPattern:
                # Get the stops for this journey pattern
                stops = get_pattern_stops(txc_jp, jps_list, lookups.stops)

                # Create a hashable representation of the stop sequence
                stop_sequence_key = create_stop_sequence_key(stops)

                # If we haven't seen this stop sequence before, create a new service pattern
                if stop_sequence_key not in stop_sequence_to_service_pattern:
                    service_pattern_id = generate_service_pattern_id(
                        service.ServiceCode, stop_sequence_key
                    )
                    stop_sequence_to_service_pattern[stop_sequence_key] = (
                        service_pattern_id
                    )
                    service_pattern_to_journey_patterns[service_pattern_id] = []

                # Map this journey pattern to the service pattern
                journey_pattern_id = txc_jp.id
                service_pattern_id = stop_sequence_to_service_pattern[stop_sequence_key]
                journey_pattern_to_service_pattern[journey_pattern_id] = (
                    service_pattern_id
                )
                service_pattern_to_journey_patterns[service_pattern_id].append(
                    journey_pattern_id
                )

    return (
        stop_sequence_to_service_pattern,
        journey_pattern_to_service_pattern,
        service_pattern_to_journey_patterns,
    )


def resolve_vehicle_journey_patterns(
    txc: TXCData, journey_pattern_to_service_pattern: dict[str, str]
) -> dict[str, str]:
    """
    Resolve VehicleJourneyRefs to determine the service pattern for each vehicle journey

    Returns:
        dict mapping vehicle journey IDs to service pattern IDs
    """
    # Vehicle journey ID to service pattern ID mapping
    vehicle_journey_to_service_pattern: dict[str, str] = {}

    # First pass - map all vehicle journeys that directly reference a journey pattern
    vehicle_journey_code_to_service_pattern: dict[str, str] = {}

    for vj in txc.VehicleJourneys:
        if vj.VehicleJourneyCode is None:
            continue  # Skip vehicle journeys without IDs

        if vj.JourneyPatternRef:
            # Direct reference to a journey pattern
            jp_id = vj.JourneyPatternRef
            if jp_id in journey_pattern_to_service_pattern:
                service_pattern_id = journey_pattern_to_service_pattern[jp_id]
                vehicle_journey_to_service_pattern[vj.VehicleJourneyCode] = (
                    service_pattern_id
                )

                # Store for reference by other vehicle journeys
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
            continue  # Skip vehicle journeys without IDs

        if (
            vj.VehicleJourneyCode not in vehicle_journey_to_service_pattern
            and vj.VehicleJourneyRef
        ):
            # Need to follow the reference chain using VehicleJourneyCode
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
    stop_sequence_to_service_pattern: dict[tuple[str, ...], str],
    service_pattern_to_journey_patterns: dict[str, list[str]],
) -> dict[str, ServicePatternMetadata]:
    """
    Create metadata about each service pattern
    """
    service_pattern_metadata: dict[str, ServicePatternMetadata] = {}

    for sp_id, jp_ids in service_pattern_to_journey_patterns.items():
        # Find the stop sequence for this service pattern
        stop_seq = next(
            (
                stop_seq
                for stop_seq, sp in stop_sequence_to_service_pattern.items()
                if sp == sp_id
            ),
            tuple(),
        )

        service_pattern_metadata[sp_id] = ServicePatternMetadata(
            journey_pattern_ids=jp_ids, num_stops=len(stop_seq)
        )

    return service_pattern_metadata


def map_unique_journey_patterns(
    txc: TXCData, lookups: ReferenceDataLookups
) -> ServicePatternMapping:
    """
    Map journey patterns to deduplicated service patterns based on unique stop sequences.
    """
    # Step 1: Identify unique patterns
    (
        stop_sequence_to_service_pattern,
        journey_pattern_to_service_pattern,
        service_pattern_to_journey_patterns,
    ) = identify_unique_patterns(txc, lookups)

    # Step 2: Resolve vehicle journey patterns
    vehicle_journey_to_service_pattern = resolve_vehicle_journey_patterns(
        txc, journey_pattern_to_service_pattern
    )

    # Step 3: Create metadata for service patterns
    service_pattern_metadata = create_service_pattern_metadata(
        stop_sequence_to_service_pattern, service_pattern_to_journey_patterns
    )

    log.info(
        "Created unique service patterns from journey patterns.",
        unique_service_pattern_count=len(stop_sequence_to_service_pattern),
        journey_pattern_count=len(journey_pattern_to_service_pattern),
        vehicle_journey_count=len(vehicle_journey_to_service_pattern),
    )

    return ServicePatternMapping(
        journey_pattern_to_service_pattern=journey_pattern_to_service_pattern,
        vehicle_journey_to_service_pattern=vehicle_journey_to_service_pattern,
        service_pattern_metadata=service_pattern_metadata,
    )
