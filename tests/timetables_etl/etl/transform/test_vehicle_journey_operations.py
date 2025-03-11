"""
Test Generating Transmodel Operating/NonOperating Days from TXC Operating Profile
"""

from datetime import date

import pytest
from common_layer.database.models import (
    TransmodelNonOperatingDatesExceptions,
    TransmodelOperatingDatesExceptions,
)
from common_layer.xml.txc.models.txc_operating_profile import (
    TXCBankHolidayDays,
    TXCBankHolidayOperation,
    TXCDaysOfWeek,
)

from tests.factories.database.transmodel import TransmodelVehicleJourneyFactory
from timetables_etl.etl.app.transform.vehicle_journey_operations import (
    get_bank_holiday_non_operating_dates,
    get_bank_holiday_operating_dates,
    process_bank_holidays,
)


@pytest.mark.parametrize(
    "days_of_operation,bank_holidays,operating_days,expected",
    [
        pytest.param(
            TXCBankHolidayDays(ChristmasDay=True),
            {"ChristmasDay": [date(2024, 12, 25)]},  # Wednesday
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
            [],
            id="Single holiday enabled",
        ),
        pytest.param(
            TXCBankHolidayDays(ChristmasDay=True, BoxingDay=True),
            {
                "ChristmasDay": [date(2024, 12, 25), date(2024, 12, 25)],  # Wednesday
                "BoxingDay": [date(2024, 12, 26)],  # Thrusday
            },
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
            [],
            id="Multiple holidays enabled",
        ),
        pytest.param(
            TXCBankHolidayDays(ChristmasDay=False),
            {"ChristmasDay": [date(2024, 12, 25)]},
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
            [],
            id="Holiday disabled",
        ),
        pytest.param(
            TXCBankHolidayDays(ChristmasDay=True),
            {},
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
            [],
            id="Holiday not in bank holidays",
        ),
        pytest.param(
            TXCBankHolidayDays(),
            {"ChristmasDay": [date(2024, 12, 25)]},
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
            [],
            id="No holidays enabled",
        ),
        pytest.param(
            TXCBankHolidayDays(ChristmasDay=True),
            {"ChristmasDay": [date(2024, 12, 25), date(2025, 12, 25)]},
            TXCDaysOfWeek(
                Monday=True,
                Tuesday=True,
                Wednesday=False,
                Thursday=True,
                Friday=True,
                Saturday=False,
                Sunday=False,
                HolidaysOnly=False,
            ),
            [date(2024, 12, 25)],
            id="Multiple dates for same holiday",
        ),
        pytest.param(
            TXCBankHolidayDays(ChristmasDay=True, BoxingDay=False, NewYearsDay=True),
            {
                "ChristmasDay": [date(2024, 12, 25)],
                "BoxingDay": [date(2024, 12, 26), date(2024, 12, 26)],
                "NewYearsDay": [date(2025, 1, 1), date(2025, 1, 1)],
            },
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
            [date(2024, 12, 25), date(2025, 1, 1)],
            id="Mix of enabled and disabled holidays",
        ),
    ],
)
def test_get_bank_holiday_operating_dates(
    days_of_operation: TXCBankHolidayDays,
    bank_holidays: dict[str, list[date]],
    operating_days: TXCDaysOfWeek,
    expected: list[date],
) -> None:
    """
    Test Matching bank holiday days with the matches found inside start / end date
    """
    result: list[date] = get_bank_holiday_operating_dates(
        days_of_operation, bank_holidays, operating_days
    )
    assert result == expected


@pytest.mark.parametrize(
    "days_of_non_operation,bank_holidays,operating_days,expected",
    [
        pytest.param(
            TXCBankHolidayDays(ChristmasDay=True),
            {"ChristmasDay": [date(2024, 12, 25)]},  # Wednesday
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
            [date(2024, 12, 25)],
            id="Single holiday enabled",
        ),
        pytest.param(
            TXCBankHolidayDays(ChristmasDay=True, BoxingDay=True),
            {
                "ChristmasDay": [date(2024, 12, 25), date(2024, 12, 25)],  # Wednesday
                "BoxingDay": [date(2024, 12, 26)],  # Thrusday
            },
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
            [date(2024, 12, 25), date(2024, 12, 26)],
            id="Multiple holidays enabled",
        ),
        pytest.param(
            TXCBankHolidayDays(ChristmasDay=False),
            {"ChristmasDay": [date(2024, 12, 25)]},
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
            [],
            id="Holiday disabled",
        ),
        pytest.param(
            TXCBankHolidayDays(ChristmasDay=True),
            {},
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
            [],
            id="Holiday not in bank holidays",
        ),
        pytest.param(
            TXCBankHolidayDays(),
            {"ChristmasDay": [date(2024, 12, 25)]},
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
            [],
            id="No holidays enabled",
        ),
        pytest.param(
            TXCBankHolidayDays(ChristmasDay=True),
            {"ChristmasDay": [date(2024, 12, 25), date(2025, 12, 25)]},
            TXCDaysOfWeek(
                Monday=True,
                Tuesday=True,
                Wednesday=True,
                Thursday=False,
                Friday=True,
                Saturday=False,
                Sunday=False,
                HolidaysOnly=False,
            ),
            [date(2024, 12, 25)],
            id="Multiple dates for same holiday",
        ),
        pytest.param(
            TXCBankHolidayDays(ChristmasDay=True, BoxingDay=False, NewYearsDay=True),
            {
                "ChristmasDay": [date(2024, 12, 25)],
                "BoxingDay": [date(2024, 12, 26), date(2024, 12, 26)],
                "NewYearsDay": [date(2025, 1, 1), date(2025, 1, 1)],
            },
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
            [date(2024, 12, 25), date(2025, 1, 1)],
            id="Mix of enabled and disabled holidays",
        ),
    ],
)
def test_get_bank_holiday_non_operating_dates(
    days_of_non_operation: TXCBankHolidayDays,
    bank_holidays: dict[str, list[date]],
    operating_days: TXCDaysOfWeek,
    expected: list[date],
) -> None:
    """
    Test Matching bank holiday days with the matches found inside start / end date
    """
    result: list[date] = get_bank_holiday_non_operating_dates(
        days_of_non_operation, bank_holidays, operating_days
    )
    assert result == expected


@pytest.mark.parametrize(
    "bank_holiday_op,bank_holidays,vehicle_journey_id,operating_days,expected",
    [
        pytest.param(
            TXCBankHolidayOperation(
                DaysOfOperation=TXCBankHolidayDays(ChristmasDay=True),
                DaysOfNonOperation=TXCBankHolidayDays(),
            ),
            {"ChristmasDay": [date(2024, 12, 25)]},
            1,
            TXCDaysOfWeek(
                Monday=True,
                Tuesday=True,
                Wednesday=False,
                Thursday=True,
                Friday=True,
                Saturday=False,
                Sunday=False,
                HolidaysOnly=False,
            ),
            (
                [
                    TransmodelOperatingDatesExceptions(
                        operating_date=date(2024, 12, 25), vehicle_journey_id=1
                    )
                ],
                [],
            ),
            id="Operating dates only",
        ),
        pytest.param(
            TXCBankHolidayOperation(
                DaysOfOperation=TXCBankHolidayDays(),
                DaysOfNonOperation=TXCBankHolidayDays(BoxingDay=True),
            ),
            {"BoxingDay": [date(2024, 12, 26)]},
            2,
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
            (
                [],
                [
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2024, 12, 26), vehicle_journey_id=2
                    )
                ],
            ),
            id="Non-operating dates only",
        ),
        pytest.param(
            TXCBankHolidayOperation(
                DaysOfOperation=TXCBankHolidayDays(),
                DaysOfNonOperation=TXCBankHolidayDays(),
            ),
            {"ChristmasDay": [date(2024, 12, 25)]},
            3,
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
            id="No dates when nothing enabled",
        ),
        pytest.param(
            TXCBankHolidayOperation(
                DaysOfOperation=TXCBankHolidayDays(ChristmasDay=True),
                DaysOfNonOperation=TXCBankHolidayDays(BoxingDay=True),
            ),
            {"ChristmasDay": [date(2024, 12, 25)], "BoxingDay": [date(2024, 12, 26)]},
            4,
            TXCDaysOfWeek(
                Monday=True,
                Tuesday=True,
                Wednesday=False,
                Thursday=True,
                Friday=True,
                Saturday=False,
                Sunday=False,
                HolidaysOnly=False,
            ),
            (
                [
                    TransmodelOperatingDatesExceptions(
                        operating_date=date(2024, 12, 25), vehicle_journey_id=4
                    )
                ],
                [
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2024, 12, 26), vehicle_journey_id=4
                    )
                ],
            ),
            id="Both operating and non-operating dates",
        ),
    ],
)
def test_process_bank_holidays(
    bank_holiday_op: TXCBankHolidayOperation,
    bank_holidays: dict[str, list[date]],
    vehicle_journey_id: int,
    operating_days: TXCDaysOfWeek,
    expected: tuple[
        list[TransmodelOperatingDatesExceptions],
        list[TransmodelNonOperatingDatesExceptions],
    ],
) -> None:
    """
    Test generating Operating and NonOperating Dates for Bank Holidays
    """

    result = process_bank_holidays(
        bank_holiday_op,
        bank_holidays,
        TransmodelVehicleJourneyFactory.create_with_id(vehicle_journey_id),
        operating_days,
    )
    assert result == expected
