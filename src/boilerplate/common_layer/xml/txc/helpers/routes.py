"""
Route Helpers
"""

from common_layer.database.models import NaptanStopPoint

from ..models.txc_route import TXCRouteSection


def extract_stop_point_pairs_from_route_sections(
    route_sections: list[TXCRouteSection],
) -> list[tuple[str, str]]:
    """Extract unique From/To stop point reference pairs from route sections."""
    stop_point_pairs: set[tuple[str, str]] = set()

    for section in route_sections:
        for route_link in section.RouteLink:
            stop_point_pairs.add((route_link.From, route_link.To))

    return list(stop_point_pairs)


def extract_stop_point_pairs(
    stop_sequence: list[NaptanStopPoint],
) -> list[tuple[str, str]]:
    """Extract From/To stop point reference pairs from an ordered sequence of stop points."""
    stop_point_pairs: list[tuple[str, str]] = []

    for i in range(len(stop_sequence) - 1):
        from_code = stop_sequence[i].atco_code
        to_code = stop_sequence[i + 1].atco_code
        stop_point_pairs.append((from_code, to_code))

    return stop_point_pairs
