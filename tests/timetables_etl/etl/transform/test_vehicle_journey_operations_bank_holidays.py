"""
Tests for Handling Bank Holiday Operations
"""

from datetime import date

import pytest
from common_layer.database.models import (
    TransmodelNonOperatingDatesExceptions,
    TransmodelOperatingDatesExceptions,
    TransmodelVehicleJourney,
)
from common_layer.xml.txc.models.txc_operating_profile import (
    TXCBankHolidayDays,
    TXCBankHolidayOperation,
    TXCDaysOfWeek,
)

from tests.factories.database.transmodel import TransmodelVehicleJourneyFactory
from timetables_etl.etl.app.transform.vehicle_journey_operations import (
    process_bank_holidays,
)


@pytest.mark.parametrize(
    "bank_holiday_operation, bank_holidays_data, vehicle_journey, operating_days, expected_result",
    [
        pytest.param(
            TXCBankHolidayOperation(
                DaysOfOperation=TXCBankHolidayDays(),
                DaysOfNonOperation=TXCBankHolidayDays(
                    ChristmasDay=True,
                    BoxingDay=True,
                    GoodFriday=True,
                    NewYearsDay=True,
                    LateSummerBankHolidayNotScotland=True,
                    MayDay=True,
                    EasterMonday=True,
                    SpringBank=True,
                    ChristmasDayHoliday=True,
                    BoxingDayHoliday=True,
                    NewYearsDayHoliday=True,
                    ChristmasEve=True,
                    NewYearsEve=True,
                ),
            ),
            {
                "ChristmasEve": [date(2024, 12, 24), date(2024, 12, 24)],  # Tuesday
                "ChristmasDay": [date(2024, 12, 25), date(2024, 12, 25)],  # Wednesday
                "BoxingDay": [date(2024, 12, 26), date(2024, 12, 26)],  # Thrusday
                "NewYearsEve": [date(2024, 12, 31), date(2024, 12, 31)],  # Tuesday
                "NewYearsDay": [date(2025, 1, 1), date(2025, 1, 1)],  # Wednesday
                "GoodFriday": [date(2025, 4, 18), date(2025, 4, 18)],  # Friday
                "EasterMonday": [date(2025, 4, 21)],  # Monday
                "MayDay": [date(2025, 5, 5), date(2025, 5, 5)],  # Monday
                "SpringBank": [date(2025, 5, 26), date(2025, 5, 26)],  # Monday
                "LateSummerBankHolidayNotScotland": [
                    date(2025, 8, 4),
                    date(2025, 8, 25),
                ],  # Monday
            },
            TransmodelVehicleJourneyFactory.create_with_id(123),
            TXCDaysOfWeek(
                Monday=False,
                Tuesday=True,
                Wednesday=True,
                Thursday=False,
                Friday=False,
                Saturday=True,
                Sunday=True,
                HolidaysOnly=False,
            ),
            (
                [],
                [
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2024, 12, 24), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2024, 12, 25), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2024, 12, 31), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2025, 1, 1), vehicle_journey_id=123
                    ),
                ],
            ),
            id="Real world bank holiday non-operating days",
        ),
        pytest.param(
            TXCBankHolidayOperation(
                DaysOfOperation=TXCBankHolidayDays(
                    ChristmasDay=True,
                    BoxingDay=True,
                ),
                DaysOfNonOperation=TXCBankHolidayDays(),
            ),
            {
                "ChristmasDay": [date(2024, 12, 25)],  # Wednesday
                "BoxingDay": [date(2024, 12, 26)],  # Thursday
            },
            TransmodelVehicleJourneyFactory.create_with_id(456),
            TXCDaysOfWeek(
                Monday=True,
                Tuesday=True,
                Wednesday=False,
                Thursday=False,
                Friday=True,
                Saturday=False,
                Sunday=False,
                HolidaysOnly=False,
            ),
            (
                [
                    TransmodelOperatingDatesExceptions(
                        operating_date=date(2024, 12, 25), vehicle_journey_id=456
                    ),
                    TransmodelOperatingDatesExceptions(
                        operating_date=date(2024, 12, 26), vehicle_journey_id=456
                    ),
                ],
                [],
            ),
            id="Simple bank holiday operating days",
        ),
        pytest.param(
            TXCBankHolidayOperation(
                DaysOfOperation=TXCBankHolidayDays(),
                DaysOfNonOperation=TXCBankHolidayDays(),
            ),
            {
                "ChristmasDay": [date(2024, 12, 25)],
                "BoxingDay": [date(2024, 12, 26)],
            },
            TransmodelVehicleJourneyFactory.create_with_id(789),
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
            ([], []),
            id="No bank holiday operations",
        ),
    ],
)
def test_process_bank_holidays(
    bank_holiday_operation: TXCBankHolidayOperation,
    bank_holidays_data: dict[str, list[date]],
    vehicle_journey: TransmodelVehicleJourney,
    operating_days: TXCDaysOfWeek,
    expected_result: tuple[
        list[TransmodelOperatingDatesExceptions],
        list[TransmodelNonOperatingDatesExceptions],
    ],
):
    """
    Test bank holiday processing
    """
    result = process_bank_holidays(
        bank_holiday_operation, bank_holidays_data, vehicle_journey, operating_days
    )
    assert result == expected_result
