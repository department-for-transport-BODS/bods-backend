"""
Descriptor Parsing
"""

from pydantic import BaseModel, Field


class DescriptorStructure(BaseModel):
    """Structured text description of a stop."""

    CommonName: str = Field(
        ..., description="Common name for the stop in a specified language"
    )
    ShortCommonName: str | None = Field(
        default=None,
        description=(
            "Alternative short name for stop. Length limit is set by administrative "
            "area. Standard abbreviations should be used to condense name elements. "
            "If omitted, defaults to CommonName, truncated if necessary"
        ),
    )
    Landmark: str | None = Field(
        default=None,
        description=(
            "Description of the nearest landmark to the stop, for example 'Town Hall'. "
            "Or nearest street crossing that can be used to distinguish stop from "
            "other stops in the street, i.e. Landmark may be a crossing"
        ),
    )
    Street: str | None = Field(
        default=None, description="Street of stop. May be road name eg B2710"
    )
    Crossing: str | None = Field(
        default=None,
        description=(
            "Where there is a street that intersects the Street, as well as a "
            "Landmark, the name of the crossing street may be included separately here"
        ),
    )
    Indicator: str | None = Field(
        default=None,
        description=(
            "Indicative description of the relative position of the stop, for example, "
            "'100 yards from Town Hall'. Bay Stand or Stance number should be placed here"
        ),
    )
