"""
StopClassification Parsing
"""

from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from ..txc_types import STOP_CLASSIFICATION_STOP_TYPE_MAPPING, TXCStopTypeT
from .stop_point_types import (
    AirStopClassificationStructure,
    BusAndCoachStationStructure,
    FerryStopClassificationStructure,
    MetroStopClassificationStructure,
    RailStopClassificationStructure,
    TaxiStopClassificationStructure,
)
from .stop_point_types_bus import BusStopStructure


class OnStreetStructure(BaseModel):
    """
    On Street Stop Information
    """

    Bus: Annotated[
        BusStopStructure | None,
        Field(default=None, description="A bus, coach or tram stop."),
    ] = None
    Taxi: Annotated[
        TaxiStopClassificationStructure | None,
        Field(default=None, description=" Taxi Stop"),
    ] = None


class OffStreetStructure(BaseModel):
    """Station, interchange or other off-street access point."""

    BusAndCoach: Annotated[
        BusAndCoachStationStructure | None,
        Field(default=None, description="Bus or coach station"),
    ] = None
    Ferry: Annotated[
        FerryStopClassificationStructure | None,
        Field(default=None, description="A ferry terminal or dock PTAN"),
    ] = None
    Rail: Annotated[
        RailStopClassificationStructure | None,
        Field(default=None, description="A railway station PTAN"),
    ] = None
    Metro: Annotated[
        MetroStopClassificationStructure | None,
        Field(default=None, description="A Metro Stop"),
    ] = None
    Air: Annotated[
        AirStopClassificationStructure | None,
        Field(default=None, description="An Airport Stop"),
    ] = None


class StopClassificationStructure(BaseModel):
    """Classification of a stop."""

    StopType: TXCStopTypeT = Field(
        ...,
        description=(
            "Classification of the stop as one of the NaPTAN stop types. Enumerated value"
        ),
    )
    OnStreet: Annotated[
        OnStreetStructure | None,
        Field(default=None, description="On street access point"),
    ] = None
    OffStreet: Annotated[
        OffStreetStructure | None,
        Field(
            default=None,
            description="Station, interchange or other off-street access point",
        ),
    ] = None

    @field_validator("StopType", mode="before")
    @classmethod
    def map_stop_type(cls, v: str):
        """
        Map Stop Type Codes
        Cases are:
          - Abbreviations to full names
          - Deprecated values to new values
        http/www.transxchange.org.uk/schema/2.4/napt/NaPT_stop-v2-4.xsd
        """

        # If it's a three-letter code, map it to the full name
        if v in STOP_CLASSIFICATION_STOP_TYPE_MAPPING:
            return STOP_CLASSIFICATION_STOP_TYPE_MAPPING[v]
        # If it's already a full name, validate that it's in the TXCStopTypeT Literal
        if v not in TXCStopTypeT.__args__:
            raise ValueError(f"Invalid stop type: {v}")

        return v
