"""
Types of StopPoint
"""

from typing import Annotated

from pydantic import BaseModel, Field

from ..txc_types import TimingStatusT


class BayStructure(BaseModel):
    """
    Timing Statuses For Bays
    """

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
    ] = None
    VariableBay: Annotated[
        BayStructure | None,
        Field(
            default=None,
            description="[BCS] Bay, stand or stance within a bus or coach station",
        ),
    ] = None
    Entrance: Annotated[
        bool, Field(default=False, description="If it's an Entrance")
    ] = False
    AccessArea: Annotated[
        bool, Field(default=False, description="Access Area for Bus and Coach")
    ] = False


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


class AnnotatedMetroRefStructure(BaseModel):
    """
    Collation with other industry reference systems.
    """

    MetroRef: Annotated[
        str, Field(default=False, description="[RSE] Railway station entrance")
    ]
    Name: Annotated[
        str,
        Field(
            default=False,
            description="[RLY] Railway interchange area away from entrance",
        ),
    ]
    Location: Annotated[
        bool, Field(default=False, description="[RPL] Specific platform")
    ]


class MetroStopClassificationStructure(BaseModel):
    """Structure for  Metro stop"""

    Entrance: Annotated[
        bool,
        Field(default=False, description="[TMU] Metro, tram or underground entrance."),
    ] = False
    AccessArea: Annotated[
        bool,
        Field(
            default=False,
            description="[MET] Metro, tram or underground interchange area",
        ),
    ] = False
    Platform: Annotated[
        bool,
        Field(default=False, description="[PLT] Metro, tram or underground platform"),
    ] = False
    AnnotatedMetroRef: Annotated[
        AnnotatedMetroRefStructure | None,
        Field(default=False, description="[RPL] Specific platform"),
    ] = None


class TaxiStopClassificationStructure(BaseModel):
    """
    Structure for  Taxi OnStreet
    """

    TaxiRank: Annotated[
        bool,
        Field(default=False, description="[TXR] The head of a taxi rank."),
    ] = False
    SharedTaxiRank: Annotated[
        bool,
        Field(
            default=False,
            description="[STR] The head of a shared taxi rank.",
        ),
    ] = False


class AirStopClassificationStructure(BaseModel):
    """
    Air Stops
    """

    Entrance: Annotated[
        bool,
        Field(default=False, description="[AIR] Airport entrance."),
    ] = False
    AccessArea: Annotated[
        bool,
        Field(
            default=False,
            description="[GAT] Airport interchange area",
        ),
    ] = False
