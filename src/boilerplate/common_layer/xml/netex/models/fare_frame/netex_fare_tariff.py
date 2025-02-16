"""
Netex Tarriffs
"""

from typing import Annotated

from pydantic import BaseModel, Field

from ..netex_utility import FromToDate, MultilingualString, VersionedRef
from .netex_fare_tariff_fare_structure import FareStructureElement


class Tariff(BaseModel):
    """Definition of a tariff"""

    id: Annotated[str, Field(description="Tariff identifier")]
    version: Annotated[str, Field(description="Version")]
    validityConditions: Annotated[
        list[FromToDate], Field(description="Validity conditions")
    ]
    Name: Annotated[MultilingualString | str, Field(description="Name of the tariff")]
    OperatorRef: Annotated[VersionedRef, Field(description="Reference to operator")]
    LineRef: Annotated[VersionedRef, Field(description="Reference to line")]
    TypeOfTariffRef: Annotated[
        VersionedRef, Field(description="Reference to tariff type")
    ]
    TariffBasis: Annotated[str, Field(description="Basis of tariff")]
    fareStructureElements: Annotated[
        list[FareStructureElement], Field(description="list of fare structure elements")
    ]
