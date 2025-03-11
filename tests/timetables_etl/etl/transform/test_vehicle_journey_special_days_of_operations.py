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
    TXCDateRange,
    TXCDaysOfWeek,
    TXCSpecialDaysOperation,
)

from tests.factories.database.transmodel import TransmodelVehicleJourneyFactory
from timetables_etl.etl.app.transform.vehicle_journey_operations import (
    process_special_operating_days,
)


@pytest.mark.parametrize(
    "special_days_operation, vehicle_journey, operating_days, expected_result",
    [
        pytest.param(
            TXCSpecialDaysOperation(
                DaysOfOperation=[
                    TXCDateRange(
                        StartDate=date(2025, 3, 10), EndDate=date(2025, 3, 12)
                    )  # Mon to Wed
                ],
                DaysOfNonOperation=[
                    TXCDateRange(
                        StartDate=date(2025, 3, 13), EndDate=date(2025, 3, 14)
                    )  # Thurs to Sun
                ],
            ),
            TransmodelVehicleJourneyFactory.create_with_id(123),
            TXCDaysOfWeek(
                Monday=True,
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
                [],
            ),
            id="non-operating and operating days not needed to be inserted",
        ),
        pytest.param(
            TXCSpecialDaysOperation(
                DaysOfOperation=[
                    TXCDateRange(
                        StartDate=date(2025, 3, 10), EndDate=date(2025, 3, 12)
                    )  # Mon to Wed
                ],
                DaysOfNonOperation=[
                    TXCDateRange(
                        StartDate=date(2025, 3, 13), EndDate=date(2025, 3, 16)
                    )  # Thurs to Sun
                ],
            ),
            TransmodelVehicleJourneyFactory.create_with_id(456),
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
                [
                    TransmodelOperatingDatesExceptions(
                        operating_date=date(2025, 3, 10), vehicle_journey_id=456
                    ),
                ],
                [
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2025, 3, 15), vehicle_journey_id=456
                    ),
                    TransmodelNonOperatingDatesExceptions(
                        non_operating_date=date(2025, 3, 16), vehicle_journey_id=456
                    ),
                ],
            ),
            id="Non operating and operating days in date range",
        ),
        pytest.param(
            TXCSpecialDaysOperation(
                DaysOfOperation=[
                    TXCDateRange(
                        StartDate=date(2025, 3, 10), EndDate=date(2025, 3, 12)
                    )  # Mon to Wed
                ],
            ),
            TransmodelVehicleJourneyFactory.create_with_id(789),
            TXCDaysOfWeek(
                Monday=True,
                Tuesday=False,
                Wednesday=False,
                Thursday=False,
                Friday=False,
                Saturday=True,
                Sunday=True,
                HolidaysOnly=False,
            ),
            (
                [
                    TransmodelOperatingDatesExceptions(
                        operating_date=date(2025, 3, 11), vehicle_journey_id=789
                    ),
                    TransmodelOperatingDatesExceptions(
                        operating_date=date(2025, 3, 12), vehicle_journey_id=789
                    ),
                ],
                [],
            ),
            id="Single date range",
        ),
    ],
)
def test_process_bank_holidays(
    special_days_operation: TXCSpecialDaysOperation,
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
    result = process_special_operating_days(
        special_days_operation, vehicle_journey, operating_days
    )
    assert result == expected_result
