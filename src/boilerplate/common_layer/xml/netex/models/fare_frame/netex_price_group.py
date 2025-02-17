"""
Price Group
"""

from typing import Annotated

from pydantic import BaseModel, Field


class GeographicalIntervalPrice(BaseModel):
    """Definition of a geographical interval price"""

    id: Annotated[str, Field(description="Price identifier")]
    version: Annotated[str, Field(description="Version")]
    Amount: Annotated[float, Field(description="Price amount")]


class PriceGroup(BaseModel):
    """Definition of a price group"""

    id: Annotated[str, Field(description="Price group identifier")]
    version: Annotated[str, Field(description="Version")]
    members: Annotated[
        list[GeographicalIntervalPrice],
        Field(description="list of prices in this group"),
    ]
