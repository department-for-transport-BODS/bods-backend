"""
Types of StopPoint
"""

from typing import Annotated

from pydantic import BaseModel, Field

from ..txc_types import TimingStatusT


class BayStructure(BaseModel):
    """[BCS] Bay, stand or stance within a bus or coach station."""

    TimingStatus: Annotated[
        TimingStatusT | None,
        Field(
            default="principalTimingPoint",
            description="Status of the registration of the bus stop as a timing point",
        ),
    ] = "principalTimingPoint"


class BusAndCoachStationStructure(BaseModel):
    """Structure for bus and coach stations."""

    Bay: Annotated[
        BayStructure | None,
        Field(
            default=None,
            description="[BCS] Bay, stand or stance within a bus or coach station",
        ),
    ]


class FerryStopClassificationStructure(BaseModel):
    """Structure for ferry terminal or dock."""

    Entrance: Annotated[
        bool, Field(default=False, description="[FTD] Ferry terminal or dock entrance")
    ] = False
    AccessArea: Annotated[
        bool, Field(default=False, description="[FER] Ferry or port interchange area")
    ] = False
    Berth: Annotated[bool, Field(default=False, description="[FBT] Ferry berth")] = (
        False
    )


class RailStopClassificationStructure(BaseModel):
    """Structure for railway station."""

    Entrance: Annotated[
        bool, Field(default=False, description="[RSE] Railway station entrance")
    ] = False
    AccessArea: Annotated[
        bool,
        Field(
            default=False,
            description="[RLY] Railway interchange area away from entrance",
        ),
    ] = False
    Platform: Annotated[
        bool, Field(default=False, description="[RPL] Specific platform")
    ] = False
