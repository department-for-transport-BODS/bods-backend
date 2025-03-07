"""
Route Helpers
"""

from ..models.txc_route import TXCRouteSection


def extract_stop_point_pairs(
    route_sections: list[TXCRouteSection],
) -> list[tuple[str, str]]:
    """Extract unique From/To stop point reference pairs from route sections."""
    stop_point_pairs: set[tuple[str, str]] = set()

    for section in route_sections:
        for route_link in section.RouteLink:
            stop_point_pairs.add((route_link.From, route_link.To))

    return list(stop_point_pairs)
