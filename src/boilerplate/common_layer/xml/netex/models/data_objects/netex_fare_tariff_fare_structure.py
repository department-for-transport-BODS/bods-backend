"""
fareStructureElement
"""

from typing import Annotated

from pydantic import BaseModel, Field

from ..netex_utility import VersionedRef


class DistanceMatrixElement(BaseModel):
    """Definition of a distance matrix element"""

    id: Annotated[str, Field(description="Distance matrix element identifier")]
    version: Annotated[str, Field(description="Version")]
    priceGroups: Annotated[
        list[VersionedRef], Field(description="list of price group references")
    ]
    StartTariffZoneRef: Annotated[
        VersionedRef | None, Field(description="Reference to start tariff zone")
    ]
    EndTariffZoneRef: Annotated[
        VersionedRef | None, Field(description="Reference to end tariff zone")
    ]
