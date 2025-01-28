"""
Marked Points
"""

from pydantic import BaseModel, Field

from ..txc_types import CompassPointT


class BearingStructure(BaseModel):
    """
    Compass Bearing
    """

    CompassPoint: CompassPointT = Field(
        ...,
        description="Eight point compass bearing (N, S, E, W etc). Enumerated value.",
    )


class MarkedPointStructure(BaseModel):
    """
    [BCT - MKD] Marked stop - for example a pole or a shelter. Point footprint.
    """

    Bearing: BearingStructure = Field(
        ...,
        description=(
            "Direction along street in which vehicle is pointing when stopped at stopping point."
        ),
    )


class UnmarkedPointStructure(BaseModel):
    """
    [BCT - CUS] Unmarked stop (or only marked on the road). Point footprint.
    """

    Bearing: BearingStructure = Field(
        ...,
        description=(
            "Direction along street in which vehicle is pointing when stopped at stopping point."
        ),
    )
