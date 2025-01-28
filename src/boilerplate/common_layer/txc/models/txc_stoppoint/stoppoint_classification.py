"""
StopClassification Parsing
"""

from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from ..txc_types import TXCStopTypeT
from .stop_point_types import BusAndCoachStationStructure
from .stop_point_types_bus import BusStopStructure


class OnStreetStructure(BaseModel):
    """
    On Street Stop Information
    """

    Bus: BusStopStructure = Field(..., description="A bus, coach or tram stop.")


class OffStreetStructure(BaseModel):
    """Station, interchange or other off-street access point."""

    BusAndCoach: Annotated[
        BusAndCoachStationStructure | None,
        Field(default=None, description="Bus or coach station"),
    ]


class StopClassificationStructure(BaseModel):
    """Classification of a stop."""

    StopType: TXCStopTypeT = Field(
        ...,
        description=(
            "Classification of the stop as one of the NaPTAN stop types. Enumerated value"
        ),
    )
    OnStreet: OnStreetStructure = Field(..., description="On street access point.")
    OffStreet: Annotated[
        OffStreetStructure | None,
        Field(
            default=None,
            description="Station, interchange or other off-street access point",
        ),
    ]

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
        stop_type_mapping: dict[str, str] = {
            # Bus/Coach stops
            "BCT": "busCoachTrolleyOnStreetPoint",
            "BCS": "busCoachTrolleyStationBay",
            "BCQ": "busCoachTrolleyStationVariableBay",
            "BST": "busCoachStationAccessArea",
            "BCE": "busCoachTrolleyStationEntrance",
            # Rail stops
            "RPL": "railPlatform",
            "RLY": "railAccessArea",
            "RSE": "railStationEntrance",
            # Tram/Metro/Underground stops
            "PLT": "tramMetroUndergroundPlatform",
            "MET": "tramMetroUndergroundAccessArea",
            "TMU": "tramMetroUndergroundStationEntrance",
            # Ferry stops
            "FBT": "ferryBerth",
            "FER": "ferryDockAccessArea",
            "FTD": "ferryTerminalDockEntrance",
            # Taxi ranks
            "TXR": "taxiRank",
            "STR": "sharedTaxiRank",
            # Airport
            "AIR": "airportEntrance",
            "GAT": "airAccessArea",
            # Other transport modes
            "SDA": "carSetDownPickUpArea",
            "LSE": "liftOrCableCarStationEntrance",
            "LCB": "liftOrCableCarAccessArea",
            "LPL": "liftOrCableCarPlatform",
            # Deprecated mappings
            "busCoachTramStationEntrance": "busCoachTrolleyStationEntrance",
            "busCoachTramStationBay": "busCoachTrolleyStationBay",
            "busCoachTramStationVariableBay": "busCoachTrolleyStationBay",
            "busCoachTramOnStreetPoint": "busCoachTrolleyOnStreetPoint",
            "FerryBerth": "ferryBerth",
        }

        # If it's a three-letter code, map it to the full name
        if v in stop_type_mapping:
            return stop_type_mapping[v]
        # If it's already a full name, validate that it's in the TXCStopTypeT Literal
        if v not in TXCStopTypeT.__args__:
            raise ValueError(f"Invalid stop type: {v}")

        return v
