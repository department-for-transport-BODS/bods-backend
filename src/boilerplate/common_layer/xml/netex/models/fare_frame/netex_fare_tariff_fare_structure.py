"""
fareStructureElement
"""

from typing import Annotated

from pydantic import BaseModel, Field

from ..data_objects.netex_data_object_profiles import UserProfile
from ..netex_utility import MultilingualString, VersionedRef


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


class UsageValidityPeriod(BaseModel):
    """Definition of usage validity period"""

    id: Annotated[str, Field(description="Usage validity period identifier")]
    version: Annotated[str, Field(description="Version")]
    UsageTrigger: Annotated[str, Field(description="Trigger for usage")]
    UsageEnd: Annotated[str, Field(description="End condition")]
    ActivationMeans: Annotated[str, Field(description="Means of activation")]


class FrequencyOfUse(BaseModel):
    """Definition of frequency of use parameters"""

    id: Annotated[str, Field(description="Frequency identifier")]
    version: Annotated[str, Field(description="Version")]
    FrequencyOfUseType: Annotated[str, Field(description="Type of frequency")]


class RoundTrip(BaseModel):
    """Definition of round trip parameters"""

    id: Annotated[str, Field(description="Round trip identifier")]
    version: Annotated[str, Field(description="Version")]
    TripType: Annotated[str, Field(description="Type of trip")]


class ValidityParameters(BaseModel):
    """
    GenericParameterAssignment -> validityParameters
    """

    LineRef: Annotated[VersionedRef, Field(description="Reference to Line")]


class GenericParameterAssignment(BaseModel):
    """Definition of generic parameter assignment"""

    id: Annotated[str, Field(description="Parameter assignment identifier")]
    version: Annotated[str, Field(description="Version")]
    order: Annotated[str, Field(description="Order of assignment")]
    TypeOfAccessRightAssignmentRef: Annotated[
        VersionedRef, Field(description="Reference to access right type")
    ]
    ValidityParameterAssignmentType: Annotated[
        str | None,
        Field(description="Type of validity parameter assignment", default=None),
    ]
    LimitationGroupingType: Annotated[
        str | None, Field(description="Type of limitation grouping", default=None)
    ]
    validityParameters: Annotated[
        ValidityParameters | None,
        Field(description="list of validity parameters", default=None),
    ]
    limitations: Annotated[
        list[UserProfile | RoundTrip | FrequencyOfUse | UsageValidityPeriod] | None,
        Field(description="list of limitations", default=None),
    ]


class FareStructureElement(BaseModel):
    """Definition of a fare structure element"""

    id: Annotated[str, Field(description="Fare structure element identifier")]
    version: Annotated[str, Field(description="Version")]
    Name: Annotated[MultilingualString | str, Field(description="Name of the element")]
    TypeOfFareStructureElementRef: Annotated[
        VersionedRef, Field(description="Reference to element type")
    ]
    distanceMatrixElements: Annotated[
        list[DistanceMatrixElement] | None,
        Field(description="list of distance matrix elements", default=None),
    ]
    GenericParameterAssignment: Annotated[
        GenericParameterAssignment | None,
        Field(description="Parameter assignment", default=None),
    ]
