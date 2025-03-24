"""
Bus Stop Type
"""

from common_layer.xml.txc.models import LocationStructure
from pydantic import BaseModel, Field, field_validator

from ..txc_types import BusStopTypeT, TimingStatusT
from .stop_point_marked import MarkedPointStructure, UnmarkedPointStructure


class FlexibleZoneStructure(BaseModel):
    Location: list[LocationStructure] | None = Field(default=None)


class BusStopStructure(BaseModel):
    """
    Data type for Type of Bus Stop.
    Some stop types have required subelements.
    """

    BusStopType: BusStopTypeT = Field(
        ..., description="Legacy classification of bus stop sub type. Enumerated value."
    )
    TimingStatus: TimingStatusT = Field(
        ...,
        description=("Status of the registration of the bus stop as a timing point"),
    )
    MarkedPoint: MarkedPointStructure | None = Field(
        default=None,
        description="[BCT - MKD] Marked stop - for example a pole or a shelter. Point footprint.",
    )

    UnmarkedPoint: UnmarkedPointStructure | None = Field(
        default=None,
        description="Unmarked stop (or only marked on the road).",
    )

    FlexibleZone: FlexibleZoneStructure | None = Field(
        default=None, description="Flexible stop zone"
    )

    @field_validator("BusStopType", mode="before")
    @classmethod
    def map_stop_type(cls, v: str):
        """
        Map BusStopType Codes
        Cases are:
          - Abbreviations to full names
        http/www.transxchange.org.uk/schema/2.4/napt/NaPT_stop-v2-4.xsd
        """
        stop_type_mapping = {
            "MKD": "marked",
            "HAR": "hailAndRide",
            "CUS": "custom",
            "FLX": "flexible",
        }

        # If it's a three-letter code, map it to the full name
        if v in stop_type_mapping:
            return stop_type_mapping[v]

        if v not in BusStopTypeT.__args__:
            raise ValueError(f"Invalid stop type: {v}")

        return v
