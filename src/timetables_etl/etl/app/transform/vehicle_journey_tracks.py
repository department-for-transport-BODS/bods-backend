"""
Vehicle Journey Tracks Generation
"""

from common_layer.database.models import (
    TransmodelTracksVehicleJourney,
    TransmodelVehicleJourney,
)
from common_layer.xml.txc.helpers.routes import extract_stop_point_pairs
from common_layer.xml.txc.models import (
    TXCData,
    TXCFlexibleJourneyPattern,
    TXCJourneyPattern,
    TXCRouteSection,
)
from structlog.stdlib import get_logger

from ..helpers import TrackLookup

log = get_logger()


def get_journey_pattern_route_sections(
    journey_pattern: TXCJourneyPattern, txc: TXCData
) -> list[TXCRouteSection]:
    """
    Get the ordered list of route sections for a journey pattern.
    """
    log_ctx = log.bind(
        journey_pattern_id=journey_pattern.id, route_ref=journey_pattern.RouteRef
    )

    route = next(
        (route for route in txc.Routes if route.id == journey_pattern.RouteRef), None
    )

    if not route:
        log_ctx.error("Referenced route not found")
        return []

    log_ctx.debug(
        "Found route sections",
        route_id=route.id,
        section_count=len(route.RouteSectionRef),
    )

    return route.RouteSectionRef


def create_vehicle_journey_tracks(
    vehicle_journeys: list[TransmodelVehicleJourney],
    route_sections: list[TXCRouteSection],
    track_lookup: TrackLookup,
) -> list[TransmodelTracksVehicleJourney]:
    """
    Create the track to vehicle journey associations with sequence numbers.
    """
    ordered_pairs = extract_stop_point_pairs(route_sections)

    journey_tracks: list[TransmodelTracksVehicleJourney] = []

    for vehicle_journey in vehicle_journeys:
        for sequence_number, (from_code, to_code) in enumerate(ordered_pairs):
            track = track_lookup.get((from_code, to_code))
            if track:
                journey_tracks.append(
                    TransmodelTracksVehicleJourney(
                        sequence_number=sequence_number,
                        tracks_id=track.id,
                        vehicle_journey_id=vehicle_journey.id,
                    )
                )

    return journey_tracks


def generate_standard_service_tracks(
    journey_pattern: TXCJourneyPattern,
    txc: TXCData,
    vehicle_journeys: list[TransmodelVehicleJourney],
    track_lookup: TrackLookup,
) -> list[TransmodelTracksVehicleJourney]:
    """
    Generate the tracks for a StandardService
    """
    log_ctx = log.bind(
        journey_pattern_id=journey_pattern.id,
        vehicle_journeys_count=len(vehicle_journeys),
    )

    route_sections = get_journey_pattern_route_sections(journey_pattern, txc)
    if not route_sections:
        log_ctx.warning("No route sections found")
        return []

    journey_tracks = create_vehicle_journey_tracks(
        vehicle_journeys=vehicle_journeys,
        route_sections=route_sections,
        track_lookup=track_lookup,
    )

    log_ctx.info(
        "Generated vehicle journey tracks",
        tracks_created=len(journey_tracks),
        route_sections_count=len(route_sections),
    )

    return journey_tracks


def generate_flexible_service_tracks(_journey_pattern: TXCFlexibleJourneyPattern):
    """
    Generate the tracks for a StandardService
    """
    log.error("Flexible Service Tracks Not Implemented!")


def generate_vehicle_journey_tracks(
    journey_pattern: TXCJourneyPattern | TXCFlexibleJourneyPattern,
    vehicle_journeys: list[TransmodelVehicleJourney],
    track_lookup: TrackLookup,
    txc: TXCData,
) -> list[TransmodelTracksVehicleJourney]:
    """
    Create Vehicle Journey Tracks
    """
    match journey_pattern:
        case TXCJourneyPattern():
            return generate_standard_service_tracks(
                journey_pattern=journey_pattern,
                txc=txc,
                vehicle_journeys=vehicle_journeys,
                track_lookup=track_lookup,
            )
        case TXCFlexibleJourneyPattern():
            generate_flexible_service_tracks(journey_pattern)
            return []
        case _:
            raise ValueError(f"Unknown Journey Pattern type: {type(journey_pattern)}")
