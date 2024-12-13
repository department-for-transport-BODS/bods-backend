"""
TXC Service Models
"""

from datetime import date

from pydantic import BaseModel, Field

from .txc_service_flexible import TXCFlexibleService
from .txc_types import TransportModeT


class TXCJourneyPattern(BaseModel):
    """
    Describes a possible bus route of a StandardService as a sequence of timing
    links between stops that a vehicle will traverse in a particular order
    representing the pattern of working for vehicles of the service

    """

    id: str
    PrivateCode: str | None = Field(
        default=None, description="Code private to the company."
    )
    DestinationDisplay: str = Field(
        ...,
        description="Text displayed to passengers about the destination.",
    )
    OperatorRef: str | None = Field(
        default=None, description="Reference to a defined operator."
    )
    Direction: str = Field(
        ...,
        description="Direction of travel, represented by an enumeration.",
    )
    RouteRef: str = Field(..., description="Reference to a defined route.")
    JourneyPatternSectionRefs: list[str] = Field(
        ...,
        description="References to the sections, at least one required.",
    )
    Description: str | None = Field(default=None, description="Optional description.")
    LayoverPoint: str | None = Field(
        default=None,
        description="Point where the vehicle may layover, to aid in real time information.",
    )


class TXCStandardService(BaseModel):
    """
    StandardService Subsection of a Service
    """

    Origin: str = Field(
        ...,
    )
    Destination: str = Field(
        ...,
    )
    JourneyPattern: list[TXCJourneyPattern] = Field(
        default=[],
    )


class TXCLineDescription(BaseModel):
    """
    OutboundDescription / InboundDescription of a line
    According to PTI:
        - Origin - Where Appropriate
        - Destination - Where Appropriate
        - Description - Yes. Shall be included
        - Vias - Where Appropriate but avoid use where possible
    """

    Origin: str | None = Field(default=None)
    Destination: str | None = Field(default=None)
    Description: str
    Vias: list[str] = Field(default=[])


class TXCLine(BaseModel):
    """
    Lines section in Service
    """

    id: str
    LineName: str = Field(...)
    MarketingName: str | None = Field(default=None)
    OutboundDescription: TXCLineDescription | None = Field(default=None)
    InboundDescription: TXCLineDescription | None = Field(default=None)


class TXCService(BaseModel):
    """
    Represents a transport service, consisting of multiple journey patterns.
    """

    RevisionNumber: int = Field(
        default=0,
    )
    ServiceCode: str = Field(...)
    PrivateCode: str | None = Field(default=None)
    RegisteredOperatorRef: str = Field(...)
    PublicUse: bool = Field(default=True)
    StartDate: date = Field(...)
    EndDate: date | None = Field(default=None)
    StandardService: TXCStandardService | None = Field(default=None)
    FlexibleService: TXCFlexibleService | None = Field(default=None)
    Lines: list[TXCLine] = Field(default=[])
    Mode: TransportModeT = Field(
        default="coach",
        description=("The mode of the service"),
    )
