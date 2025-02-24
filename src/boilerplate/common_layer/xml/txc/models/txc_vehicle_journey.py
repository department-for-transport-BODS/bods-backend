"""
TranXchange 2.4 PTI 1.1.A
VehicleJourney
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator
from structlog.stdlib import get_logger

from .txc_operating_profile import TXCOperatingProfile
from .txc_types import CommercialBasisT, ModificationType, TimeDemandT
from .txc_validators import convert_runtime
from .txc_vehicle_journey_common import TXCOperational

log = get_logger()


class TXCLayoverPoint(BaseModel):
    """
    VehicleJourney LayoverPoint Section
    """

    Duration: str = Field(
        ..., description="Time of wait at layover point. Uses standard duration type."
    )
    Name: str = Field(..., description="Free text description of layover point")
    Location: str = Field(..., description="Location of layover point.")


class TXCDeadRun(BaseModel):
    """
    VehicleJourney StartDeadRun/EndDeadRun Section
    TODO: Unimplemented
    """


class TXCVehicleJourneyInterchange(BaseModel):
    """
    VehicleJourney VehicleJourneyInterchange Section
    TODO: Unimplemented
    """


class TXCFrequency(BaseModel):
    """
    VehicleJourney Frequency Section
    TODO: Unimplemented
    """


class TXCVehicleJourneyStopUsageStructure(BaseModel):
    """
    From/To for TXCVehicleJourneyTimingLink
    """

    WaitTime: str | None = Field(
        default=None, description="The total wait time at the stop."
    )
    DynamicDestinationDisplay: str | None = Field(
        default=None,
        description="Description of the destination at this stop",
    )
    _convert_waittime = field_validator("WaitTime")(convert_runtime)


class TXCVehicleJourneyTimingLink(BaseModel):
    """
    VehicleJourney Frequency Section
    """

    id: str | None = None
    JourneyPatternTimingLinkRef: str
    VehicleJourneyRef: str | None = Field(
        default=None, description="Optional Vehicle Journey ref"
    )
    RunTime: str | None = Field(..., description="Actual Run time")
    From: TXCVehicleJourneyStopUsageStructure | None = Field(
        default=None,
        description=(
            "May be included in order to provide WaitTime or different DynamicDestinationDisplay."
            "Other elements shall not be used."
            "WaitTime shall match the WaitTime on the preceding To link"
        ),
    )
    To: TXCVehicleJourneyStopUsageStructure | None = Field(
        default=None,
        description=(
            "May be included in order to provide WaitTime or different DynamicDestinationDisplay."
            "Other elements shall not be used."
            "WaitTime shall match the WaitTime on the following From link"
        ),
    )
    DutyCrewCode: str | None = Field(
        default=None,
        description="Bus crew identifier (i.e. dutyboard) for the timing link.",
    )

    _convert_runtime = field_validator("RunTime")(convert_runtime)


class TXCVehicleJourney(BaseModel):
    """
    Vehicle Journey
    """

    id: str | None = None
    SequenceNumber: str | None = Field(default=None, description="")
    CreationDateTime: datetime | None = Field(
        default=None,
        description="",
    )
    ModificationDateTime: datetime | None = Field(
        default=None,
        description="",
    )
    Modification: ModificationType | None = Field(default=None, description="")
    RevisionNumber: int | None = Field(
        default=None,
        description="",
    )
    PrivateCode: str | None = Field(
        default=None,
        description="",
    )
    DestinationDisplay: str | None = Field(
        default=None,
        description="If not using DestinationDisplay/DynamicDestinationDisplay in JourneyPattern",
    )
    OperatorRef: str | None = Field(
        default=None, description="Reference to a defined operator."
    )
    Operational: TXCOperational | None = Field(default=None, description="")
    OperatingProfile: TXCOperatingProfile | None = Field(
        default=None, description="To replace service definitions"
    )
    TimeDemand: TimeDemandT | None = Field(default=None, description="")
    CommercialBasis: CommercialBasisT = Field(
        default="notContracted", description="on which the service is offered."
    )
    LayoverPoint: TXCLayoverPoint | None = Field(default=None, description="")
    GarageRef: list[str] = Field(default=[], description="")
    Description: str | None = Field(default=None, description="")
    VehicleJourneyCode: str | None = Field(default=None, description="Mandated")
    ServiceRef: str | None = Field(default=None, description="Mandated")
    LineRef: str | None = Field(default=None, description="Mandated")
    JourneyPatternRef: str | None = Field(
        default=None,
        description="One of JourneyPatternRef or VehicleJourneyRef Required",
    )
    VehicleJourneyRef: str | None = Field(
        default=None,
        description="One of JourneyPatternRef or VehicleJourneyRef Required",
    )
    StartDeadRun: TXCDeadRun | None = Field(default=None, description="")
    EndDeadRun: TXCDeadRun | None = Field(default=None, description="")
    VehicleJourneyInterchange: TXCVehicleJourneyInterchange | None = Field(
        default=None, description=""
    )
    Note: str | None = Field(default=None, description="")
    DepartureTime: str = Field(..., description="Departure Time")
    DepartureDayShift: int | None = Field(
        default=None,
        description="PTI only allows +1, TXC Allows any positive / negative int",
    )
    Frequency: TXCFrequency | None = Field(default=None, description="")
    VehicleJourneyTimingLink: list[TXCVehicleJourneyTimingLink] = Field(
        default=[], description=""
    )

    @model_validator(mode="after")
    def check_vehicle_journey_ref(self):
        """
        Check if one of journey pattern or vehicle journey is provided
        """
        if not self.JourneyPatternRef and not self.VehicleJourneyRef:
            raise ValueError("One of JourneyPatternRef or VehicleJourneyRef Required")
        return self
