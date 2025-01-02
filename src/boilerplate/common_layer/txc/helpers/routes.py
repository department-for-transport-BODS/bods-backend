"""
Route Helpers
"""

from ..models.txc_route import TXCRouteSection


def extract_stop_point_pairs(
    route_sections: list[TXCRouteSection],
) -> list[tuple[str, str]]:
    """Extract From/To stop point reference pairs from route sections."""
    stop_point_pairs: list[tuple[str, str]] = []

    for section in route_sections:
        for route_link in section.RouteLink:
            stop_point_pairs.append((route_link.From, route_link.To))

    return stop_point_pairs
