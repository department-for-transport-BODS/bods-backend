"""
Models for lists of different reference types
"""

from typing import Annotated

from pydantic import BaseModel, Field, model_validator

from .netex_utility import VersionedRef


class ObjectReferences(BaseModel):
    """Container for object references"""

    OperatorRef: Annotated[VersionedRef | None, Field(description="an operator")] = None
    LineRef: Annotated[VersionedRef | None, Field(description="a line")] = None
    FareZoneRef: Annotated[VersionedRef | None, Field(description=" a farezone ")] = (
        None
    )


class PricableObjectRefs(BaseModel):
    """
    priceableObjectRefs_RelStructure
    Container for references to objects that can have prices assigned
    """

    PreassignedFareProductRef: Annotated[
        VersionedRef | None,
        Field(description="A pre-defined fare product (e.g. ticket type, pass)"),
    ] = None

    SalesOfferPackageRef: Annotated[
        VersionedRef | None,
        Field(description="A sales offer package defining how a fare product is sold"),
    ] = None

    UserProfileRef: Annotated[
        VersionedRef | None,
        Field(
            description="A user profile defining passenger type (e.g. adult, child, senior)"
        ),
    ] = None


class ScheduledStopPointReference(VersionedRef):
    """
    StopPointRef
    """

    Name: str | None = None
    atco_code: str | None = None
    naptan_code: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _populate_atco_code(cls, data):
        if not isinstance(data, dict):
            return data

        if "ref" in data:
            ref_parts = data["ref"].split(":")

            if len(ref_parts) == 2:
                if ref_parts[0] == "atco" or ref_parts[0] == "naptan":
                    data["atco_code"] = ref_parts[1]
                else:
                    data["naptan_code"] = ref_parts[1]

        return data


class PointRefs(BaseModel):
    """
    pointRefs_RelStructure
    """

    ScheduledStopPointRef: Annotated[
        list[ScheduledStopPointReference],
        Field(
            description="scheduled stop points to pick up or set down passengers",
        ),
    ] = []

    TimingPointRef: Annotated[
        list[VersionedRef],
        Field(
            description="points used for timing purposes in schedule, may not be stop points",
        ),
    ] = []

    RoutePointRef: Annotated[
        list[VersionedRef],
        Field(
            description="points defining the route geometry, like where route changes direction",
        ),
    ] = []

    FareScheduledStopPointRef: Annotated[
        list[VersionedRef],
        Field(
            description="stop points used for fare calculations, may represent fare stage points",
        ),
    ] = []

    PointRef: Annotated[
        list[VersionedRef],
        Field(
            description="Generic points of any type in the network",
            default_factory=list,
        ),
    ] = []
