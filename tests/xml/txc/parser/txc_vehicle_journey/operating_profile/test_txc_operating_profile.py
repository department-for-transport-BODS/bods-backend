"""
Operating Profile Tests for Vehicle Journeys
"""

from datetime import date

import pytest
from common_layer.xml.txc.models.txc_operating_profile import (
    TXCBankHolidayDays,
    TXCBankHolidayOperation,
    TXCDateRange,
    TXCDaysOfWeek,
    TXCOperatingProfile,
    TXCPeriodicDayType,
    TXCServicedOrganisationDayType,
    TXCSpecialDaysOperation,
)
from common_layer.xml.txc.parser.operating_profile import parse_operating_profile
from lxml import etree


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
