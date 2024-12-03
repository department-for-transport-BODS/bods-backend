"""
TranXchange 2.4 PTI 1.1.A
VehicleJourney
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .txc_types import CommercialBasisT, ModificationType, TimeDemandT
from .txc_validators import convert_runtime
from .txc_vehicle_journey_common import TXCOperational


class TXCDaysOfWeek(BaseModel):
    """
    TXC PTI Days of Week
    PTI 1.1 requires only named individual days be used
    """

    Monday: bool
    Tuesday: bool
    Wednesday: bool
    Thursday: bool
    Friday: bool
    Saturday: bool
    Sunday: bool
    HolidaysOnly: bool

    @model_validator(mode="after")
    def validate_days_of_week(self):
        """
        Ensure the TXC Days of the week is set
        """
        days = [
            self.Monday,
            self.Tuesday,
            self.Wednesday,
            self.Thursday,
            self.Friday,
            self.Saturday,
            self.Sunday,
        ]
        if self.HolidaysOnly and any(days):
            raise ValueError("If HolidaysOnly is True, all other days must be False")

        if not self.HolidaysOnly and not any(days):
            raise ValueError(
                "If HolidaysOnly is False, at least one other day must be True"
            )

        return self


class TXCBankHolidayDays(BaseModel):
    """
    Bank Holidays
    BankHolidayChoiceGroup in http/www.transxchange.org.uk/schema/2.4/napt/NaPT_dayTypes-v2-2.xsd
    """

    ChristmasDay: bool = False
    BoxingDay: bool = False
    GoodFriday: bool = False
    NewYearsDay: bool = False
    Jan2ndScotland: bool = False
    StAndrewsDay: bool = False
    LateSummerBankHolidayNotScotland: bool = False
    MayDay: bool = False
    EasterMonday: bool = False
    SpringBank: bool = False
    AugustBankHolidayScotland: bool = False
    ChristmasDayHoliday: bool = False
    BoxingDayHoliday: bool = False
    NewYearsDayHoliday: bool = False
    Jan2ndScotlandHoliday: bool = False
    StAndrewsDayHoliday: bool = False
    ChristmasEve: bool = False
    NewYearsEve: bool = False


class TXCBankHolidayOperation(BaseModel):
    """
    Bank Holidays
    BankHolidayChoiceGroup in http/www.transxchange.org.uk/schema/2.4/napt/NaPT_dayTypes-v2-2.xsd
    """

    DaysOfOperation: TXCBankHolidayDays
    DaysOfNonOperation: TXCBankHolidayDays


class TXCPeriodicDayType(BaseModel):
    """
    Wherever a trip or service operates on regular, periodic days,
    then this shall be defined using the PeriodicDayType.
    Works in conjunction with the RegularDayType element:
        RegularDayType states which day(s) of the week the trip or service operates
        While PeriodicDayType indicates, which weeks in that month it operates
    These are the weeks of a month it operates on
    """

    first: bool = Field(default=False, description="Operates on First Week")
    second: bool = Field(default=False, description="Operates on Second Week")
    third: bool = Field(default=False, description="Operates on Third Week")
    forth: bool = Field(default=False, description="Operates on Forth Week")
    fifth: bool = Field(default=False, description="Operates on Forth Week")
    last: bool = Field(default=False, description="Operates on Last Week")


class TXCDateRange(BaseModel):
    """
    Date Ranges used for operations
    """

    StartDate: date = Field(..., description="Inclusive of Start Date")
    EndDate: date = Field(..., description="Inclusive of End Date")
    Note: str | None = Field(default=None, description="Description of the range")


class TXCSpecialDaysOperation(BaseModel):
    """
    Special Days Operation
    """

    DaysOfOperation: list[TXCDateRange] = Field(
        default=[], description="Ranges where the service operates specially"
    )
    DaysOfNonOperation: list[TXCDateRange] = Field(
        default=[], description="Ranges where the service doesn't operate"
    )


class TXCServicedOrganisationDayType(BaseModel):
    """
    Serviced Organisation Day Type
    """

    WorkingDays: list[str] | None = Field(
        default=None, description="List of ServicedOrganisationRef"
    )
    Holidays: list[str] | None = Field(
        default=None, description="List of ServicedOrganisationRef"
    )


class TXCOperatingProfile(BaseModel):
    """
    VehicleJourney OperatingProfile Section
    """

    RegularDayType: TXCDaysOfWeek = Field(..., description="Required")
    PeriodicDayType: TXCPeriodicDayType | None = Field(
        default=None, description="Repeating patterns"
    )
    ServicedOrganisationDayType: TXCServicedOrganisationDayType | None = Field(
        default=None, description="Serviced Organisation"
    )
    SpecialDaysOperation: TXCSpecialDaysOperation | None = Field(
        default=None, description="Special Days"
    )
    BankHolidayOperation: TXCBankHolidayOperation | None = Field(
        default=None, description="Bank Holidays"
    )


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
    DepartureDayShift: Literal["+1"] | None = Field(
        default=None, description="If present, shall be +1"
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
