"""
OSRM Geometry API Client
"""

import requests
from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape  # type:ignore
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from shapely import LineString
from structlog.stdlib import get_logger

from .models import Route, RouteResponse

log = get_logger()


class OSRMGeometryAPISettings(BaseSettings):
    """
    PostgreSQL database configuration settings.
    Automatically loads env vars
    """

    model_config = SettingsConfigDict(case_sensitive=False, extra="allow")

    OSRM_BASE_URL: str = Field(
        default="http://localhost:5001", description="Host URL for OSRM API"
    )


class OSRMGeometryAPI:
    """
    API for building a road-based route for a given set of co-ordinates
    """

    def __init__(self, settings: OSRMGeometryAPISettings | None = None):
        settings = settings or OSRMGeometryAPISettings()
        self.base_url = settings.OSRM_BASE_URL

    def _make_route_request(
        self, coords_list: list[tuple[float, float]]
    ) -> Route | None:
        """
        Make a Route request to the OSRM API and return the parsed Route
        """
        coords: str = ";".join(f"{lon},{lat}" for lon, lat in coords_list)
        url = f"{self.base_url}/route/v1/driving/{coords}"
        params = {"overview": "full", "geometries": "geojson"}
        res = requests.get(url, params=params, timeout=60).json()
        route_response = RouteResponse(**res)

        if not route_response.code.lower() == "ok":
            log.error(
                "OSRM Service returned none OK response code",
                response_code=route_response.code,
            )
            return None

        if not route_response.routes:
            log.error(
                "OSRM Service returned no Routes for given coordinates", coords=coords
            )
            return None

        return route_response.routes[0]

    def get_geometry_and_distance(
        self, coords: list[tuple[float, float]]
    ) -> tuple[None, None] | tuple[WKBElement, int]:
        """
        Get a road-based route and distance for the given coords
        using the OSRM API
        """
        route = self._make_route_request(coords)
        if not route:
            return None, None

        route_coordinates = route.geometry.coordinates
        linestring = from_shape(LineString(route_coordinates), srid=4326)

        return linestring, int(route.distance)
