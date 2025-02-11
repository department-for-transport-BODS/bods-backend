"""
Flexible Vehicle journeys
"""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from .txc_types import DirectionT, ModificationType
from .txc_vehicle_journey_common import TXCOperational


class TXCServicePeriod(BaseModel):
    """
    FlexibleServiceTimes ServicePeriod Section
    """

    StartTime: str = Field(..., description="Start time of the flexible service period")
    EndTime: str = Field(..., description="End time of the flexible service period")


class TXCFlexibleServiceTimes(BaseModel):
    """
    FlexibleVehicleJourney FlexibleServiceTimes Section
    Can either have ServicePeriod or AllDayService, but not both
    """

    ServicePeriod: TXCServicePeriod | None = Field(
        default=None,
        description="Time period during which the flexible service operates",
    )
    AllDayService: bool = Field(
        default=False, description="Indicates if the service runs all day"
    )

    @model_validator(mode="after")
    def validate_service_times(self):
        """
        Ensure either ServicePeriod or AllDayService is set, but not both
        """
        if self.ServicePeriod and self.AllDayService:
            raise ValueError("Cannot have both ServicePeriod and AllDayService")
        if not self.ServicePeriod and not self.AllDayService:
            raise ValueError("Must have either ServicePeriod or AllDayService")
        return self


class TXCFlexibleVehicleJourney(BaseModel):
    """
    Flexible Vehicle Journey
    Represents a flexible bus service that operates within defined areas and time windows
    rather than following a fixed route and schedule
    """

    id: str | None = None
    SequenceNumber: str | None = Field(
        default=None, description="Sequential identifier"
    )
    CreationDateTime: datetime | None = Field(
        default=None,
        description="When the flexible journey was created",
    )
    ModificationDateTime: datetime | None = Field(
        default=None,
        description="When the flexible journey was last modified",
    )
    Modification: ModificationType | None = Field(
        default=None, description="Type of modification"
    )
    RevisionNumber: int | None = Field(
        default=None,
        description="Version number of this journey",
    )
    PrivateCode: str | None = Field(
        default=None,
        description="Internal identifier used by the operator",
    )
    DestinationDisplay: str | None = Field(
        default=None,
        description="Text to be shown on the vehicle's destination display",
    )
    Direction: DirectionT | None = Field(
        default=None,
        description="Direction of the journey",
    )
    OperatorRef: str | None = Field(
        default=None, description="Reference to a defined operator"
    )
    Operational: TXCOperational | None = Field(default=None, description="")
    Description: str | None = Field(
        default=None, description="Description of the flexible service"
    )
    VehicleJourneyCode: str = Field(
        ..., description="Unique identifier for this journey"
    )
    ServiceRef: str = Field(..., description="Reference to the parent service")
    LineRef: str = Field(
        ..., description="Reference to the line on which this journey operates"
    )
    JourneyPatternRef: str | None = Field(
        default=None,
        description="A VJ Requires a JourneyPatternRef or VehicleJourneyRef",
    )
    VehicleJourneyRef: str | None = Field(
        default=None,
        description="A reference to another VJ and then that VJ Journey Pattern will be used",
    )
    FlexibleServiceTimes: list[TXCFlexibleServiceTimes] = Field(
        ..., description="Time windows during which the flexible service operates"
    )
    Note: str | None = Field(
        default=None, description="Additional notes about the flexible journey"
    )

    @model_validator(mode="after")
    def check_vehicle_journey_ref(self):
        """
        Check if one of journey pattern or vehicle journey is provided
        """
        if not self.JourneyPatternRef and not self.VehicleJourneyRef:
            raise ValueError("One of JourneyPatternRef or VehicleJourneyRef Required")
        return self
