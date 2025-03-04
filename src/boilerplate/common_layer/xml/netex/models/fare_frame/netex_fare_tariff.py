"""
Netex Tarriffs
"""

from typing import Annotated

from pydantic import BaseModel, Field

from ..netex_types import TariffBasisT
from ..netex_utility import FromToDate, MultilingualString, VersionedRef
from .netex_fare_tariff_fare_structure import FareStructureElement


class Tariff(BaseModel):
    """Definition of a tariff"""

    id: Annotated[str, Field(description="Tariff identifier")]
    version: Annotated[str, Field(description="Version")]
    validityConditions: Annotated[
        list[FromToDate], Field(description="Validity conditions")
    ]
    Name: Annotated[
        MultilingualString | str | None, Field(description="Name of the tariff")
    ]
    OperatorRef: Annotated[
        VersionedRef | None, Field(description="Reference to operator")
    ]
    LineRef: Annotated[VersionedRef | None, Field(description="Reference to line")]
    TypeOfTariffRef: Annotated[
        VersionedRef | None, Field(description="Reference to tariff type")
    ]
    TariffBasis: Annotated[
        TariffBasisT | None, Field(description="Basis of tariff")
    ] = None
    fareStructureElements: Annotated[
        list[FareStructureElement], Field(description="list of fare structure elements")
    ]
