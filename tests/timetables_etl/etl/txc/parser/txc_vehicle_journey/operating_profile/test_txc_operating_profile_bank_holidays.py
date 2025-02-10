"""
Bank Holiday VJ Parsing Tests
"""

import pytest
from common_layer.txc.models import TXCBankHolidayDays, TXCBankHolidayOperation
from common_layer.txc.parser.operating_profile import (
    parse_bank_holiday_days,
    parse_bank_holiday_operation,
)
from lxml import etree


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
