"""
Vehicle Journey Operating Profile Parsing
"""

from datetime import date

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ..models.txc_vehicle_journey import (
    TXCBankHolidayDays,
    TXCBankHolidayOperation,
    TXCDateRange,
    TXCDaysOfWeek,
    TXCOperatingProfile,
    TXCPeriodicDayType,
    TXCServicedOrganisationDayType,
    TXCSpecialDaysOperation,
)
from .utils_tags import does_element_exist, get_element_text, get_element_texts

log = get_logger()


def parse_bank_holiday_days(bank_holiday_days_xml: _Element) -> TXCBankHolidayDays:
    """
    Parse Bank Holidays

    """
    return TXCBankHolidayDays(
        ChristmasDay=does_element_exist(bank_holiday_days_xml, "ChristmasDay"),
        BoxingDay=does_element_exist(bank_holiday_days_xml, "BoxingDay"),
        GoodFriday=does_element_exist(bank_holiday_days_xml, "GoodFriday"),
        NewYearsDay=does_element_exist(bank_holiday_days_xml, "NewYearsDay"),
        Jan2ndScotland=does_element_exist(bank_holiday_days_xml, "Jan2ndScotland"),
        StAndrewsDay=does_element_exist(bank_holiday_days_xml, "StAndrewsDay"),
        LateSummerBankHolidayNotScotland=does_element_exist(
            bank_holiday_days_xml, "LateSummerBankHolidayNotScotland"
        ),
        MayDay=does_element_exist(bank_holiday_days_xml, "MayDay"),
        EasterMonday=does_element_exist(bank_holiday_days_xml, "EasterMonday"),
        SpringBank=does_element_exist(bank_holiday_days_xml, "SpringBank"),
        AugustBankHolidayScotland=does_element_exist(
            bank_holiday_days_xml, "AugustBankHolidayScotland"
        ),
        ChristmasDayHoliday=does_element_exist(
            bank_holiday_days_xml, "ChristmasDayHoliday"
        ),
        BoxingDayHoliday=does_element_exist(bank_holiday_days_xml, "BoxingDayHoliday"),
        NewYearsDayHoliday=does_element_exist(
            bank_holiday_days_xml, "NewYearsDayHoliday"
        ),
        Jan2ndScotlandHoliday=does_element_exist(
            bank_holiday_days_xml, "Jan2ndScotlandHoliday"
        ),
        StAndrewsDayHoliday=does_element_exist(
            bank_holiday_days_xml, "StAndrewsDayHoliday"
        ),
        ChristmasEve=does_element_exist(bank_holiday_days_xml, "ChristmasEve"),
        NewYearsEve=does_element_exist(bank_holiday_days_xml, "NewYearsEve"),
    )


def parse_bank_holiday_operation(
    bank_holiday_operation_xml: _Element,
) -> TXCBankHolidayOperation | None:
    """
    VehicleJourney -> OperatingProfile -> BankHolidayOperation -> DaysOfOperaton/DaysOfNonOperation
    """
    days_of_operation_xml = bank_holiday_operation_xml.find("DaysOfOperation")
    days_of_non_operation_xml = bank_holiday_operation_xml.find("DaysOfNonOperation")

    if days_of_operation_xml is None and days_of_non_operation_xml is None:
        return None

    days_of_operation = (
        parse_bank_holiday_days(days_of_operation_xml)
        if days_of_operation_xml is not None
        else TXCBankHolidayDays()
    )

    days_of_non_operation = (
        parse_bank_holiday_days(days_of_non_operation_xml)
        if days_of_non_operation_xml is not None
        else TXCBankHolidayDays()
    )

    return TXCBankHolidayOperation(
        DaysOfOperation=days_of_operation,
        DaysOfNonOperation=days_of_non_operation,
    )


def parse_date_range(date_range_xml: _Element) -> TXCDateRange | None:
    """
    Special Day Operation Date Ranges
    """
    start_date_str = get_element_text(date_range_xml, "StartDate")
    end_date_str = get_element_text(date_range_xml, "EndDate")
    note = get_element_text(date_range_xml, "Note")

    if start_date_str and end_date_str:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
        return TXCDateRange(StartDate=start_date, EndDate=end_date, Note=note)

    return None


def parse_date_ranges(
    special_days_operation_xml: _Element, is_operation: bool
) -> list[TXCDateRange]:
    """
    Parse Days of operation / non operation date ranges
    """
    date_ranges: list[TXCDateRange] = []
    operation_type = "Operation" if is_operation else "NonOperation"
    xpath = f"DaysOf{operation_type}/DateRange"

    for date_range_xml in special_days_operation_xml.findall(xpath):
        date_range = parse_date_range(date_range_xml)
        if date_range:
            date_ranges.append(date_range)

    return date_ranges


def parse_special_days_operation(
    special_days_operation_xml: _Element,
) -> TXCSpecialDaysOperation | None:
    """
    VehicleJourneys -> VehicleJourney -> OperatingProfile -> SpecialDaysOperation
    """
    days_of_operation = parse_date_ranges(special_days_operation_xml, is_operation=True)
    days_of_non_operation = parse_date_ranges(
        special_days_operation_xml, is_operation=False
    )

    if not days_of_operation and not days_of_non_operation:
        return None

    return TXCSpecialDaysOperation(
        DaysOfOperation=days_of_operation,
        DaysOfNonOperation=days_of_non_operation,
    )


def parse_regular_days(regular_day_type_xml: _Element) -> TXCDaysOfWeek:
    """
    VehicleJourneys -> VehicleJourney -> OperatingProfile -> RegularDayTime
    """
    dow_xml = regular_day_type_xml.find("DaysOfWeek")
    holidays_only = does_element_exist(regular_day_type_xml, "HolidaysOnly")

    monday = does_element_exist(dow_xml, "Monday")
    tuesday = does_element_exist(dow_xml, "Tuesday")
    wednesday = does_element_exist(dow_xml, "Wednesday")
    thursday = does_element_exist(dow_xml, "Thursday")
    friday = does_element_exist(dow_xml, "Friday")
    saturday = does_element_exist(dow_xml, "Saturday")
    sunday = does_element_exist(dow_xml, "Sunday")

    if does_element_exist(dow_xml, "MondayToFriday"):
        monday = tuesday = wednesday = thursday = friday = True
    elif does_element_exist(dow_xml, "Weekend"):
        saturday = sunday = True
    elif does_element_exist(dow_xml, "MondayToSunday"):
        monday = tuesday = wednesday = thursday = friday = saturday = sunday = True

    return TXCDaysOfWeek(
        Monday=monday,
        Tuesday=tuesday,
        Wednesday=wednesday,
        Thursday=thursday,
        Friday=friday,
        Saturday=saturday,
        Sunday=sunday,
        HolidaysOnly=holidays_only,
    )


def parse_periodic_days(periodic_day_type_xml: _Element) -> TXCPeriodicDayType:
    """
    VehicleJourneys -> VehicleJourney -> OperatingProfile ->PeriodicDayType
    """
    week_numbers = get_element_texts(periodic_day_type_xml, "WeekOfMonth/WeekNumber")

    first = "first" in week_numbers if week_numbers else False
    second = "second" in week_numbers if week_numbers else False
    third = "third" in week_numbers if week_numbers else False
    forth = "fourth" in week_numbers if week_numbers else False
    fifth = "fifth" in week_numbers if week_numbers else False
    last = "last" in week_numbers if week_numbers else False

    return TXCPeriodicDayType(
        first=first,
        second=second,
        third=third,
        forth=forth,
        fifth=fifth,
        last=last,
    )


def parse_serviced_organisation_days(
    serviced_organisation_xml: _Element,
) -> TXCServicedOrganisationDayType | None:
    """
    VehicleJourney -> OperatingProfile -> ServicedOrganisationDayType
    """

    days_of_operation = serviced_organisation_xml.find("DaysOfOperation")
    if days_of_operation is None:
        return None

    working_days_xml = days_of_operation.find("WorkingDays")
    holidays_xml = days_of_operation.find("Holidays")

    working_days = (
        get_element_texts(working_days_xml, "ServicedOrganisationRef")
        if working_days_xml is not None
        else None
    )
    holidays = (
        get_element_texts(holidays_xml, "ServicedOrganisationRef")
        if holidays_xml is not None
        else None
    )

    if not working_days and not holidays:
        return None

    return TXCServicedOrganisationDayType(
        WorkingDays=working_days,
        Holidays=holidays,
    )


def parse_operating_profile(
    operating_profile_xml: _Element,
) -> TXCOperatingProfile | None:
    """
    VehicleJourneys -> VehicleJourney -> OperatingProfile
    """
    regular_day_type_xml = operating_profile_xml.find("RegularDayType")
    if regular_day_type_xml is not None:
        regular_day_type = parse_regular_days(regular_day_type_xml)
    else:
        log.warning(
            "Missing RegularDayType for Operating Profile returning None",
            xml=operating_profile_xml,
        )
        return None

    periodic_day_type_xml = operating_profile_xml.find("PeriodicDayType")
    periodic_day_type: TXCPeriodicDayType | None = None
    if periodic_day_type_xml is not None:
        periodic_day_type = parse_periodic_days(periodic_day_type_xml)

    special_days_operation_xml = operating_profile_xml.find("SpecialDaysOperation")
    special_days_operation = (
        parse_special_days_operation(special_days_operation_xml)
        if special_days_operation_xml is not None
        else None
    )

    bank_holiday_operation_xml = operating_profile_xml.find("BankHolidayOperation")
    bank_holiday_operation = (
        parse_bank_holiday_operation(bank_holiday_operation_xml)
        if bank_holiday_operation_xml is not None
        else None
    )

    serviced_organisation_day_type_xml = operating_profile_xml.find(
        "ServicedOrganisationDayType"
    )
    serviced_organisation_day_type = (
        parse_serviced_organisation_days(serviced_organisation_day_type_xml)
        if serviced_organisation_day_type_xml is not None
        else None
    )

    operating_profile = TXCOperatingProfile(
        RegularDayType=regular_day_type,
        PeriodicDayType=periodic_day_type,
        SpecialDaysOperation=special_days_operation,
        BankHolidayOperation=bank_holiday_operation,
        ServicedOrganisationDayType=serviced_organisation_day_type,
    )
    return operating_profile
