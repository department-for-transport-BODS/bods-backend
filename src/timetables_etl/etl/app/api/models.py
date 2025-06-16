"""
API Models
"""

from typing import List, Literal

from pydantic import BaseModel


class Geometry(BaseModel):
    """Geometry type for OSRM route"""

    type: Literal["LineString"]
    coordinates: List[List[float]]  # [[lon, lat], ...]


class Route(BaseModel):
    """Route mapped by OSRM"""

    distance: float  # meters
    geometry: Geometry


class RouteResponse(BaseModel):
    """Response model for OSRM API Route endpoint"""

    code: str
    routes: List[Route] = []
