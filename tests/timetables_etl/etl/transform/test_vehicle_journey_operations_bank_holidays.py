"""
Tests for Handling Bank Holiday Operations
"""

from datetime import date

import pytest

from timetables_etl.etl.app.database.models.model_transmodel import (
    TransmodelNonOperatingDatesExceptions,
    TransmodelOperatingDatesExceptions,
)
from timetables_etl.etl.app.transform.vehicle_journey_operations import (
    process_bank_holidays,
)
from timetables_etl.etl.app.txc.models.txc_vehicle_journey import (
    TXCBankHolidayDays,
    TXCBankHolidayOperation,
)


@pytest.mark.parametrize(
    "bank_holiday_operation, bank_holidays_data, vehicle_journey_id, expected_result",
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
                "ChristmasEve": [date(2024, 12, 24), date(2024, 12, 24)],
                "ChristmasDay": [date(2024, 12, 25), date(2024, 12, 25)],
                "BoxingDay": [date(2024, 12, 26), date(2024, 12, 26)],
                "NewYearsEve": [date(2024, 12, 31), date(2024, 12, 31)],
                "NewYearsDay": [date(2025, 1, 1), date(2025, 1, 1)],
                "GoodFriday": [date(2025, 4, 18), date(2025, 4, 18)],
                "EasterMonday": [date(2025, 4, 21)],
                "MayDay": [date(2025, 5, 5), date(2025, 5, 5)],
                "SpringBank": [date(2025, 5, 26), date(2025, 5, 26)],
                "LateSummerBankHolidayNotScotland": [
                    date(2025, 8, 4),
                    date(2025, 8, 25),
                ],
            },
            123,
            (
                [],
                [
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2024, 12, 24), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2024, 12, 24), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2024, 12, 25), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2024, 12, 25), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2024, 12, 26), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2024, 12, 26), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2024, 12, 31), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2024, 12, 31), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2025, 1, 1), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2025, 1, 1), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2025, 4, 18), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2025, 4, 18), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2025, 4, 21), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2025, 5, 5), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2025, 5, 5), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2025, 5, 26), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2025, 5, 26), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2025, 8, 4), vehicle_journey_id=123
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2025, 8, 25), vehicle_journey_id=123
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
                "ChristmasDay": [date(2024, 12, 25)],
                "BoxingDay": [date(2024, 12, 26)],
            },
            456,
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
            789,
            ([], []),
            id="No bank holiday operations",
        ),
    ],
)
def test_process_bank_holidays(
    bank_holiday_operation: TXCBankHolidayOperation,
    bank_holidays_data: dict[str, list[date]],
    vehicle_journey_id: int,
    expected_result: tuple[
        list[TransmodelOperatingDatesExceptions],
        list[TransmodelNonOperatingDatesExceptions],
    ],
):
    """
    Test bank holiday processing
    """
    result = process_bank_holidays(
        bank_holiday_operation, bank_holidays_data, vehicle_journey_id
    )
    assert result == expected_result
