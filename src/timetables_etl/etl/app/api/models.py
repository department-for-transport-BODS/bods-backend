from typing import List, Literal

from pydantic import BaseModel


class Geometry(BaseModel):
    type: Literal["LineString"]
    coordinates: List[List[float]]  # [[lon, lat], ...]


class Route(BaseModel):
    distance: float  # meters
    geometry: Geometry


class RouteResponse(BaseModel):
    code: str
    routes: List[Route] = []
