"""
Preassigned Fares
"""

from typing import Annotated

from pydantic import BaseModel, Field

from ..netex_types import ChargingMomentTypeT, PreassignedFareProductTypeT, TariffBasisT
from ..netex_utility import MultilingualString, VersionedRef


class ValidableElement(BaseModel):
    """Definition of a validable element"""

    id: Annotated[str, Field(description="Validable element identifier")]
    version: Annotated[str, Field(description="Version")]
    Name: Annotated[MultilingualString | str, Field(description="Name of the element")]
    fareStructureElements: Annotated[
        list[VersionedRef], Field(description="References to fare structure elements")
    ]


class AccessRightInProduct(BaseModel):
    """Definition of an access right in product"""

    id: Annotated[str, Field(description="Access right identifier")]
    version: Annotated[str, Field(description="Version")]
    order: Annotated[str, Field(description="Order")]
    ValidableElementRef: Annotated[
        VersionedRef, Field(description="Reference to validable element")
    ]


class ConditionSummary(BaseModel):
    """Summary of fare conditions"""

    FareStructureType: Annotated[
        str | None, Field(description="Type of fare structure")
    ]
    TariffBasis: Annotated[TariffBasisT, Field(description="Basis of tariff")]
    IsPersonal: Annotated[
        bool | None, Field(description="Whether the fare is personal")
    ]


class PreassignedFareProduct(BaseModel):
    """Definition of a preassigned fare product"""

    id: Annotated[str, Field(description="Product identifier")]
    version: Annotated[str, Field(description="Version")]
    Name: Annotated[
        MultilingualString | None, Field(description="Name of the product")
    ] = None
    ChargingMomentRef: Annotated[
        VersionedRef, Field(description="Reference to charging moment")
    ]
    ChargingMomentType: Annotated[
        ChargingMomentTypeT | None, Field(description="Type of charging moment")
    ] = None
    TypeOfFareProductRef: Annotated[
        VersionedRef, Field(description="Reference to product type")
    ]
    OperatorRef: Annotated[VersionedRef, Field(description="Reference to operator")]
    ConditionSummary: Annotated[
        ConditionSummary, Field(description="Summary of conditions")
    ]
    validableElements: Annotated[
        list[ValidableElement], Field(description="list of validable elements")
    ]
    accessRightsInProduct: Annotated[
        list[AccessRightInProduct], Field(description="list of access rights")
    ]
    ProductType: Annotated[
        PreassignedFareProductTypeT | None, Field(description="Type of product")
    ]
