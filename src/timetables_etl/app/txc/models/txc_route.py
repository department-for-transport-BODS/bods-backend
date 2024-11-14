"""
TranXchange 2.4 PTI 1.1.A
Stop Point
"""

from datetime import datetime

from pydantic import BaseModel, Field

from .config import FrozenBaseModel
from .txc_types import ModificationType


class TXCLocation(BaseModel):
    """
    Represents a geographic location by longitude and latitude.
    """

    id: str = Field(..., description="Unique identifier for the location.")
    Longitude: str = Field(..., description="Geographic longitude of the location.")
    Latitude: str = Field(..., description="Geographic latitude of the location.")


class TXCMapping(BaseModel):
    """
    Contains mappings of locations that form a track.
    """

    Location: list[TXCLocation] = Field(
        ..., description="List of location points for the track."
    )


class TXCTrack(BaseModel):
    """
    Describes a piece of the route's path that can be projected onto the geospatial model.
    """

    Mapping: TXCMapping = Field(
        ...,
        description=(
            "Mapping of geographic locations that form the track. "
            "The division of route links into tracks is determined by implementors."
        ),
    )


class TXCRouteLink(BaseModel):
    """
    Type for a route link.
    """

    id: str
    CreationDateTime: datetime | None = Field(
        default=None,
        description="Creation date and time of the route link.",
    )
    ModificationDateTime: datetime | None = Field(
        default=None,
        description="Last modification date and time of the route link.",
    )
    Modification: ModificationType | None = Field(
        default=None, description="Type of modification made to the route link."
    )
    RevisionNumber: int | None = Field(
        default=None,
        description="Revision number of the route link.",
    )
    From: str = Field(...)
    To: str = Field(...)
    Distance: int | None = Field(
        default=None,
        description=("Distance in metres along the track of the link."),
    )
    Track: TXCTrack | None = Field(default=None)


class RouteSection(BaseModel):
    """
    A reusable section of route comprising one or more route links
    Ordered in sequence of traversal.
    """

    id: str
    CreationDateTime: datetime | None = Field(
        default=None,
        description="Creation date and time of the route link.",
    )
    ModificationDateTime: datetime | None = Field(
        default=None,
        description="Last modification date and time of the route link.",
    )
    RouteLink: list[TXCRouteLink] = Field(default=[])


class TXCRoute(FrozenBaseModel):
    """
    A collection of one or more routes
    """

    id: str = Field(..., description="Attribute: ID")
    CreationDateTime: datetime | None = Field(
        default=None,
        description="Attribute: Creation date and time",
    )
    ModificationDateTime: datetime | None = Field(
        default=None,
        description="Attribute: Last modification date and time",
    )
    Modification: ModificationType | None = Field(
        default=None,
        description="Attribute: Type of modification made",
    )
    RevisionNumber: int | None = Field(
        default=None,
        description="Attribute: Revision number",
    )
    PrivateCode: str | None = Field(
        default=None,
        description="Optional cross reference to an external system identifier for the route.",
    )
    Description: str = Field(
        ...,
        description="Description of the route",
    )
    RouteSectionRef: list[RouteSection] = Field(
        description="Description of the route",
    )
