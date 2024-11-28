"""
Operating Profile Tests for Vehicle Journeys
"""

from datetime import date

import pytest
from lxml import etree
from pydantic import ValidationError

from timetables_etl.etl.app.txc.models.txc_vehicle_journey import (
    TXCBankHolidayDays,
    TXCBankHolidayOperation,
    TXCDateRange,
    TXCDaysOfWeek,
    TXCOperatingProfile,
    TXCPeriodicDayType,
    TXCServicedOrganisationDayType,
    TXCSpecialDaysOperation,
)
from timetables_etl.etl.app.txc.parser.operating_profile import (
    parse_bank_holiday_days,
    parse_bank_holiday_operation,
    parse_date_range,
    parse_date_ranges,
    parse_operating_profile,
    parse_periodic_days,
    parse_regular_days,
    parse_serviced_organisation_days,
    parse_special_days_operation,
)


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <BankHolidayDays>
                <ChristmasDay/>
                <BoxingDay/>
                <NewYearsDay/>
            </BankHolidayDays>
            """,
            TXCBankHolidayDays(
                ChristmasDay=True,
                BoxingDay=True,
                GoodFriday=False,
                NewYearsDay=True,
                Jan2ndScotland=False,
                StAndrewsDay=False,
                LateSummerBankHolidayNotScotland=False,
                MayDay=False,
                EasterMonday=False,
                SpringBank=False,
                AugustBankHolidayScotland=False,
                ChristmasDayHoliday=False,
                BoxingDayHoliday=False,
                NewYearsDayHoliday=False,
                Jan2ndScotlandHoliday=False,
                StAndrewsDayHoliday=False,
                ChristmasEve=False,
                NewYearsEve=False,
            ),
            id="Basic bank holidays",
        ),
        pytest.param(
            """
            <BankHolidayDays>
                <StAndrewsDay/>
                <Jan2ndScotland/>
                <AugustBankHolidayScotland/>
            </BankHolidayDays>
            """,
            TXCBankHolidayDays(
                ChristmasDay=False,
                BoxingDay=False,
                GoodFriday=False,
                NewYearsDay=False,
                Jan2ndScotland=True,
                StAndrewsDay=True,
                LateSummerBankHolidayNotScotland=False,
                MayDay=False,
                EasterMonday=False,
                SpringBank=False,
                AugustBankHolidayScotland=True,
                ChristmasDayHoliday=False,
                BoxingDayHoliday=False,
                NewYearsDayHoliday=False,
                Jan2ndScotlandHoliday=False,
                StAndrewsDayHoliday=False,
                ChristmasEve=False,
                NewYearsEve=False,
            ),
            id="Scottish bank holidays",
        ),
        pytest.param(
            """
            <BankHolidayDays>
                <ChristmasDayHoliday/>
                <BoxingDayHoliday/>
                <NewYearsDayHoliday/>
                <Jan2ndScotlandHoliday/>
                <StAndrewsDayHoliday/>
                <ChristmasEve/>
                <NewYearsEve/>
            </BankHolidayDays>
            """,
            TXCBankHolidayDays(
                ChristmasDay=False,
                BoxingDay=False,
                GoodFriday=False,
                NewYearsDay=False,
                Jan2ndScotland=False,
                StAndrewsDay=False,
                LateSummerBankHolidayNotScotland=False,
                MayDay=False,
                EasterMonday=False,
                SpringBank=False,
                AugustBankHolidayScotland=False,
                ChristmasDayHoliday=True,
                BoxingDayHoliday=True,
                NewYearsDayHoliday=True,
                Jan2ndScotlandHoliday=True,
                StAndrewsDayHoliday=True,
                ChristmasEve=True,
                NewYearsEve=True,
            ),
            id="Holiday substitutions and eves",
        ),
    ],
)
def test_parse_bank_holiday_days(xml_string: str, expected_result: TXCBankHolidayDays):
    """
    Bank Holiday Days Parsing Tests
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_bank_holiday_days(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <BankHolidayOperation>
                <DaysOfOperation>
                    <ChristmasDay/>
                    <BoxingDay/>
                </DaysOfOperation>
                <DaysOfNonOperation>
                    <NewYearsDay/>
                    <GoodFriday/>
                </DaysOfNonOperation>
            </BankHolidayOperation>
            """,
            TXCBankHolidayOperation(
                DaysOfOperation=TXCBankHolidayDays(
                    ChristmasDay=True,
                    BoxingDay=True,
                ),
                DaysOfNonOperation=TXCBankHolidayDays(
                    GoodFriday=True,
                    NewYearsDay=True,
                ),
            ),
            id="Both operation and non-operation days",
        ),
        pytest.param(
            """
            <BankHolidayOperation>
                <DaysOfOperation>
                    <ChristmasDay/>
                    <BoxingDay/>
                    <NewYearsDay/>
                </DaysOfOperation>
            </BankHolidayOperation>
            """,
            TXCBankHolidayOperation(
                DaysOfOperation=TXCBankHolidayDays(
                    ChristmasDay=True,
                    BoxingDay=True,
                    NewYearsDay=True,
                ),
                DaysOfNonOperation=TXCBankHolidayDays(),
            ),
            id="Only operation days",
        ),
        pytest.param(
            """
            <BankHolidayOperation>
                <DaysOfNonOperation>
                    <ChristmasDay/>
                    <BoxingDay/>
                </DaysOfNonOperation>
            </BankHolidayOperation>
            """,
            TXCBankHolidayOperation(
                DaysOfOperation=TXCBankHolidayDays(),
                DaysOfNonOperation=TXCBankHolidayDays(
                    ChristmasDay=True,
                    BoxingDay=True,
                ),
            ),
            id="Only non-operation days",
        ),
        pytest.param(
            """
            <BankHolidayOperation>
            </BankHolidayOperation>
            """,
            None,
            id="Empty bank holiday operation",
        ),
    ],
)
def test_parse_bank_holiday_operation(
    xml_string: str, expected_result: TXCBankHolidayOperation | None
):
    """
    Ensure Bank holiday operations are parsed correctly
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_bank_holiday_operation(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, is_operation, expected_result",
    [
        pytest.param(
            """
            <SpecialDaysOperation>
                <DaysOfOperation>
                    <DateRange>
                        <StartDate>2023-01-01</StartDate>
                        <EndDate>2023-01-05</EndDate>
                    </DateRange>
                    <DateRange>
                        <StartDate>2023-02-01</StartDate>
                        <EndDate>2023-02-05</EndDate>
                    </DateRange>
                </DaysOfOperation>
                <DaysOfNonOperation>
                    <DateRange>
                        <StartDate>2023-03-01</StartDate>
                        <EndDate>2023-03-05</EndDate>
                    </DateRange>
                </DaysOfNonOperation>
            </SpecialDaysOperation>
            """,
            True,
            [
                TXCDateRange(StartDate=date(2023, 1, 1), EndDate=date(2023, 1, 5)),
                TXCDateRange(StartDate=date(2023, 2, 1), EndDate=date(2023, 2, 5)),
            ],
            id="Valid days of operation",
        ),
        pytest.param(
            """
            <SpecialDaysOperation>
                <DaysOfOperation>
                    <DateRange>
                        <StartDate>2023-01-01</StartDate>
                        <EndDate>2023-01-05</EndDate>
                    </DateRange>
                </DaysOfOperation>
                <DaysOfNonOperation>
                    <DateRange>
                        <StartDate>2023-03-01</StartDate>
                        <EndDate>2023-03-05</EndDate>
                    </DateRange>
                    <DateRange>
                        <StartDate>2023-04-01</StartDate>
                        <EndDate>2023-04-05</EndDate>
                    </DateRange>
                </DaysOfNonOperation>
            </SpecialDaysOperation>
            """,
            False,
            [
                TXCDateRange(StartDate=date(2023, 3, 1), EndDate=date(2023, 3, 5)),
                TXCDateRange(StartDate=date(2023, 4, 1), EndDate=date(2023, 4, 5)),
            ],
            id="Valid days of non-operation",
        ),
    ],
)
def test_parse_date_ranges(
    xml_string: str, is_operation: bool, expected_result: list[TXCDateRange]
):
    """
    Ensure Date Ranges are parsed correctly
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_date_ranges(xml_element, is_operation)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string",
    [
        pytest.param(
            """
            <DateRange>
                <StartDate>2023-01-01</StartDate>
            </DateRange>
            """,
            id="Missing end date",
        ),
        pytest.param(
            """
            <DateRange>
                <EndDate>2023-01-05</EndDate>
            </DateRange>
            """,
            id="Missing start date",
        ),
        pytest.param(
            """
            <DateRange>
            </DateRange>
            """,
            id="Empty date range",
        ),
        pytest.param(
            """
            <DateRange>
                <StartDate></StartDate>
                <EndDate>2023-01-05</EndDate>
            </DateRange>
            """,
            id="Empty start date",
        ),
        pytest.param(
            """
            <DateRange>
                <StartDate>2023-01-01</StartDate>
                <EndDate></EndDate>
            </DateRange>
            """,
            id="Empty end date",
        ),
    ],
)
def test_parse_date_range_returns_none(xml_string: str):
    """
    Test cases where parse_date_range should return None
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_date_range(xml_element)
    assert result is None


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <SpecialDaysOperation>
                <DaysOfOperation>
                    <DateRange>
                        <StartDate>2023-01-01</StartDate>
                        <EndDate>2023-01-05</EndDate>
                    </DateRange>
                </DaysOfOperation>
                <DaysOfNonOperation>
                    <DateRange>
                        <StartDate>2023-03-01</StartDate>
                        <EndDate>2023-03-05</EndDate>
                    </DateRange>
                </DaysOfNonOperation>
            </SpecialDaysOperation>
            """,
            TXCSpecialDaysOperation(
                DaysOfOperation=[
                    TXCDateRange(StartDate=date(2023, 1, 1), EndDate=date(2023, 1, 5))
                ],
                DaysOfNonOperation=[
                    TXCDateRange(StartDate=date(2023, 3, 1), EndDate=date(2023, 3, 5))
                ],
            ),
            id="Valid special days operation",
        ),
        pytest.param(
            """
            <SpecialDaysOperation>
            </SpecialDaysOperation>
            """,
            None,
            id="Empty special days operation",
        ),
    ],
)
def test_parse_special_days_operation(
    xml_string: str, expected_result: TXCSpecialDaysOperation | None
):
    """
    Special Days Operations
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_special_days_operation(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <RegularDayType>
                <DaysOfWeek>
                    <Monday/>
                    <Tuesday/>
                    <Wednesday/>
                    <Thursday/>
                </DaysOfWeek>
            </RegularDayType>
            """,
            TXCDaysOfWeek(
                Monday=True,
                Tuesday=True,
                Wednesday=True,
                Thursday=True,
                Friday=False,
                Saturday=False,
                Sunday=False,
                HolidaysOnly=False,
            ),
            id="Individual Days: Weekdays",
        ),
        pytest.param(
            """
            <RegularDayType>
                <DaysOfWeek>
                    <Saturday/>
                    <Sunday/>
                </DaysOfWeek>
            </RegularDayType>
            """,
            TXCDaysOfWeek(
                Monday=False,
                Tuesday=False,
                Wednesday=False,
                Thursday=False,
                Friday=False,
                Saturday=True,
                Sunday=True,
                HolidaysOnly=False,
            ),
            id="Individual Days: Weekend",
        ),
        pytest.param(
            """
            <RegularDayType>
                <HolidaysOnly/>
            </RegularDayType>
            """,
            TXCDaysOfWeek(
                Monday=False,
                Tuesday=False,
                Wednesday=False,
                Thursday=False,
                Friday=False,
                Saturday=False,
                Sunday=False,
                HolidaysOnly=True,
            ),
            id="Holidays only",
        ),
        pytest.param(
            """
            <RegularDayType>
                <DaysOfWeek>
                    <MondayToFriday/>
                </DaysOfWeek>
            </RegularDayType>
            """,
            TXCDaysOfWeek(
                Monday=True,
                Tuesday=True,
                Wednesday=True,
                Thursday=True,
                Friday=True,
                Saturday=False,
                Sunday=False,
                HolidaysOnly=False,
            ),
            id="MondayToFriday",
        ),
        pytest.param(
            """
            <RegularDayType>
                <DaysOfWeek>
                    <MondayToSunday/>
                </DaysOfWeek>
            </RegularDayType>
            """,
            TXCDaysOfWeek(
                Monday=True,
                Tuesday=True,
                Wednesday=True,
                Thursday=True,
                Friday=True,
                Saturday=True,
                Sunday=True,
                HolidaysOnly=False,
            ),
            id="MondayToSunday",
        ),
        pytest.param(
            """
            <RegularDayType>
                <DaysOfWeek>
                    <Weekend/>
                </DaysOfWeek>
            </RegularDayType>
            """,
            TXCDaysOfWeek(
                Monday=False,
                Tuesday=False,
                Wednesday=False,
                Thursday=False,
                Friday=False,
                Saturday=True,
                Sunday=True,
                HolidaysOnly=False,
            ),
            id="Weekend",
        ),
    ],
)
def test_parse_regular_days(xml_string: str, expected_result: TXCDaysOfWeek):
    """
    Regular Days
    """
    xml_element = etree.fromstring(xml_string)

    result = parse_regular_days(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string",
    [
        pytest.param(
            """
            <RegularDayType>
                <DaysOfWeek>
                    <Monday/>
                </DaysOfWeek>
                <HolidaysOnly/>
            </RegularDayType>
            """,
            id="Invalid regular days (holidays only with other days)",
        ),
        pytest.param(
            """
            <RegularDayType>
            </RegularDayType>
            """,
            id="Invalid regular days (no days specified)",
        ),
    ],
)
def test_parse_regular_days_validation(xml_string: str):
    """
    Test Validation Error is raised
    """
    xml_element = etree.fromstring(xml_string)
    with pytest.raises(ValidationError):
        parse_regular_days(xml_element)


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <PeriodicDayType>
                <WeekOfMonth>
                    <WeekNumber>first</WeekNumber>
                </WeekOfMonth>
                <WeekOfMonth>
                    <WeekNumber>third</WeekNumber>
                </WeekOfMonth>
            </PeriodicDayType>
            """,
            TXCPeriodicDayType(first=True, third=True),
            id="Valid periodic days (first and third weeks)",
        ),
        pytest.param(
            """
            <PeriodicDayType>
                <WeekOfMonth>
                    <WeekNumber>second</WeekNumber>
                </WeekOfMonth>
                <WeekOfMonth>
                    <WeekNumber>fourth</WeekNumber>
                </WeekOfMonth>
                <WeekOfMonth>
                    <WeekNumber>last</WeekNumber>
                </WeekOfMonth>
            </PeriodicDayType>
            """,
            TXCPeriodicDayType(second=True, forth=True, last=True),
            id="Valid periodic days (second, fourth, and last weeks)",
        ),
        pytest.param(
            """
            <PeriodicDayType>
            </PeriodicDayType>
            """,
            TXCPeriodicDayType(),
            id="Empty periodic days",
        ),
    ],
)
def test_parse_periodic_days(xml_string, expected_result):
    """
    Periodic dats parsing
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_periodic_days(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <ServicedOrganisationDayType>
                <DaysOfOperation>
                    <WorkingDays>
                        <ServicedOrganisationRef>080Sch-Thurrock</ServicedOrganisationRef>
                    </WorkingDays>
                    <Holidays>
                        <ServicedOrganisationRef>Organisation2</ServicedOrganisationRef>
                    </Holidays>
                </DaysOfOperation>
            </ServicedOrganisationDayType>
            """,
            TXCServicedOrganisationDayType(
                WorkingDays=["080Sch-Thurrock"],
                Holidays=["Organisation2"],
            ),
            id="Both working days and holidays",
        ),
        pytest.param(
            """
            <ServicedOrganisationDayType>
                <DaysOfOperation>
                    <WorkingDays>
                        <ServicedOrganisationRef>School1</ServicedOrganisationRef>
                        <ServicedOrganisationRef>School2</ServicedOrganisationRef>
                    </WorkingDays>
                </DaysOfOperation>
            </ServicedOrganisationDayType>
            """,
            TXCServicedOrganisationDayType(
                WorkingDays=["School1", "School2"],
                Holidays=None,
            ),
            id="Only working days with multiple refs",
        ),
        pytest.param(
            """
            <ServicedOrganisationDayType>
                <DaysOfOperation>
                    <Holidays>
                        <ServicedOrganisationRef>Holiday1</ServicedOrganisationRef>
                        <ServicedOrganisationRef>Holiday2</ServicedOrganisationRef>
                    </Holidays>
                </DaysOfOperation>
            </ServicedOrganisationDayType>
            """,
            TXCServicedOrganisationDayType(
                WorkingDays=None,
                Holidays=["Holiday1", "Holiday2"],
            ),
            id="Only holidays with multiple refs",
        ),
        pytest.param(
            """
            <ServicedOrganisationDayType>
            </ServicedOrganisationDayType>
            """,
            None,
            id="Empty serviced organisation",
        ),
        pytest.param(
            """
            <ServicedOrganisationDayType>
                <DaysOfOperation>
                </DaysOfOperation>
            </ServicedOrganisationDayType>
            """,
            None,
            id="Empty days of operation",
        ),
    ],
)
def test_parse_serviced_organisation_days(
    xml_string: str, expected_result: TXCServicedOrganisationDayType | None
):
    """
    Test parsing serviced organisation day types
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_serviced_organisation_days(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <OperatingProfile>
                <RegularDayType>
                    <DaysOfWeek>
                        <Monday/>
                        <Tuesday/>
                        <Wednesday/>
                    </DaysOfWeek>
                </RegularDayType>
                <PeriodicDayType>
                    <WeekOfMonth>
                        <WeekNumber>first</WeekNumber>
                    </WeekOfMonth>
                    <WeekOfMonth>
                        <WeekNumber>third</WeekNumber>
                    </WeekOfMonth>
                </PeriodicDayType>
                <SpecialDaysOperation>
                    <DaysOfOperation>
                        <DateRange>
                            <StartDate>2023-01-01</StartDate>
                            <EndDate>2023-01-05</EndDate>
                        </DateRange>
                    </DaysOfOperation>
                    <DaysOfNonOperation>
                        <DateRange>
                            <StartDate>2023-03-01</StartDate>
                            <EndDate>2023-03-05</EndDate>
                        </DateRange>
                    </DaysOfNonOperation>
                </SpecialDaysOperation>
                <BankHolidayOperation>
                    <DaysOfOperation>
                        <ChristmasDay/>
                        <BoxingDay/>
                    </DaysOfOperation>
                    <DaysOfNonOperation>
                        <GoodFriday/>
                        <NewYearsDay/>
                    </DaysOfNonOperation>
                </BankHolidayOperation>
            </OperatingProfile>
            """,
            TXCOperatingProfile(
                RegularDayType=TXCDaysOfWeek(
                    Monday=True,
                    Tuesday=True,
                    Wednesday=True,
                    Thursday=False,
                    Friday=False,
                    Saturday=False,
                    Sunday=False,
                    HolidaysOnly=False,
                ),
                PeriodicDayType=TXCPeriodicDayType(first=True, third=True),
                SpecialDaysOperation=TXCSpecialDaysOperation(
                    DaysOfOperation=[
                        TXCDateRange(
                            StartDate=date(2023, 1, 1), EndDate=date(2023, 1, 5)
                        )
                    ],
                    DaysOfNonOperation=[
                        TXCDateRange(
                            StartDate=date(2023, 3, 1), EndDate=date(2023, 3, 5)
                        )
                    ],
                ),
                BankHolidayOperation=TXCBankHolidayOperation(
                    DaysOfOperation=TXCBankHolidayDays(
                        ChristmasDay=True,
                        BoxingDay=True,
                    ),
                    DaysOfNonOperation=TXCBankHolidayDays(
                        GoodFriday=True,
                        NewYearsDay=True,
                    ),
                ),
            ),
            id="Valid operating profile",
        ),
        pytest.param(
            """
            <OperatingProfile>
                <RegularDayType>
                    <DaysOfWeek>
                        <Saturday/>
                        <Sunday/>
                    </DaysOfWeek>
                </RegularDayType>
            </OperatingProfile>
            """,
            TXCOperatingProfile(
                RegularDayType=TXCDaysOfWeek(
                    Monday=False,
                    Tuesday=False,
                    Wednesday=False,
                    Thursday=False,
                    Friday=False,
                    Saturday=True,
                    Sunday=True,
                    HolidaysOnly=False,
                ),
            ),
            id="Operating profile with only regular days",
        ),
        pytest.param(
            """
            <OperatingProfile>
                <RegularDayType>
                    <DaysOfWeek>
                        <Monday/>
                        <Tuesday/>
                    </DaysOfWeek>
                </RegularDayType>
                <ServicedOrganisationDayType>
                    <DaysOfOperation>
                        <WorkingDays>
                            <ServicedOrganisationRef>School1</ServicedOrganisationRef>
                        </WorkingDays>
                        <Holidays>
                            <ServicedOrganisationRef>Holiday1</ServicedOrganisationRef>
                        </Holidays>
                    </DaysOfOperation>
                </ServicedOrganisationDayType>
            </OperatingProfile>
            """,
            TXCOperatingProfile(
                RegularDayType=TXCDaysOfWeek(
                    Monday=True,
                    Tuesday=True,
                    Wednesday=False,
                    Thursday=False,
                    Friday=False,
                    Saturday=False,
                    Sunday=False,
                    HolidaysOnly=False,
                ),
                ServicedOrganisationDayType=TXCServicedOrganisationDayType(
                    WorkingDays=["School1"],
                    Holidays=["Holiday1"],
                ),
            ),
            id="Operating profile with serviced organisation",
        ),
        pytest.param(
            """
            <OperatingProfile>
            </OperatingProfile>
            """,
            None,
            id="Empty operating profile",
        ),
    ],
)
def test_parse_operating_profile(
    xml_string: str, expected_result: TXCOperatingProfile | None
):
    """
    Test Correct output
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_operating_profile(xml_element)
    assert result == expected_result
