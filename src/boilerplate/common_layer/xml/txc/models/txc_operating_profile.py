"""
OperatingProfile

Can be in:
  - VehicleJourney
  - Service
"""

from datetime import date

from pydantic import BaseModel, Field, model_validator
from structlog.stdlib import get_logger

log = get_logger()


class TXCDateRange(BaseModel):
    """
    Date Ranges used for operations
    """

    StartDate: date = Field(..., description="Inclusive of Start Date")
    EndDate: date = Field(..., description="Inclusive of End Date")
    Note: str | None = Field(default=None, description="Description of the range")


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
            log.info(
                "No days selected but validation passing due to backwards compatibility",
                current_behavior="Current implementation treats empty DaysOfWeek as all false",
                correct_behavior="TXC 2.1 spec treats empty DaysOfWeek as MondayToSunday",
            )
            # Temporarily removed to accommodate current implementation bug:
            # incorrect_implementation in parse_regular days can be removed when fixing
            # Issue: BODS-8037
            # raise ValueError("If HolidaysOnly is False, at least one other day must be True")

        return self


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
