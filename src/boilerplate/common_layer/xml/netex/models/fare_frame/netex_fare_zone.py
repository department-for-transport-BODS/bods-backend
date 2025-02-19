"""
FareZone inside a FareFrame
"""

from typing import Annotated

from pydantic import BaseModel, Field

from ..netex_references import PointRefs
from ..netex_utility import MultilingualString


class FareZone(BaseModel):
    """Definition of a fare zone"""

    id: Annotated[str, Field(description="Fare zone identifier")]
    version: Annotated[str, Field(description="Version of the fare zone")]
    Name: Annotated[
        MultilingualString | str, Field(description="Name of the fare zone")
    ]
    members: Annotated[
        PointRefs | None,
        Field(description="list of scheduled stop points in this fare zone"),
    ] = None
