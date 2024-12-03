"""
Test Creating Booking Arrangements
"""

from datetime import date

import pytest

from tests.timetables_etl.factories.database import TransmodelServiceFactory
from tests.timetables_etl.factories.database.transmodel import (
    TransmodelBookingArrangementsFactory,
)
from timetables_etl.etl.app.database.models import (
    TransmodelBookingArrangements,
    TransmodelService,
)
from timetables_etl.etl.app.transform.booking_arrangements import (
    create_booking_arrangements,
)
from timetables_etl.etl.app.txc.models import (
    TXCBookingArrangements,
    TXCFlexibleJourneyPattern,
    TXCFlexibleService,
    TXCLine,
    TXCPhone,
    TXCService,
)


@pytest.mark.parametrize(
    ("txc_service", "transmodel_service", "expected_arrangements"),
    [
        pytest.param(
            TXCService(
                ServiceCode="STD001",
                RegisteredOperatorRef="OPERATOR",
                PublicUse=True,
                StartDate=date(2024, 1, 1),
                Lines=[TXCLine(id="LINE:STD001", LineName="STD001")],
                FlexibleService=None,
            ),
            TransmodelServiceFactory.create_with_id(
                id_number=1,
                service_code="STD001",
                service_type="standard",
            ),
            [],
            id="Standard service returns empty list",
        ),
        pytest.param(
            TXCService(
                ServiceCode="FLX001",
                RegisteredOperatorRef="OPERATOR",
                PublicUse=True,
                StartDate=date(2024, 1, 1),
                Lines=[TXCLine(id="LINE:FLX001", LineName="FLX001")],
                FlexibleService=TXCFlexibleService(
                    Origin="Start",
                    Destination="End",
                    UseAllStopPoints=False,
                    FlexibleJourneyPattern=[],
                ),
            ),
            TransmodelServiceFactory.create_with_id(
                id_number=2,
                service_code="FLX001",
                service_type="flexible",
            ),
            [],
            id="Flexible service without arrangements returns empty list",
        ),
        pytest.param(
            TXCService(
                ServiceCode="FLX002",
                RegisteredOperatorRef="OPERATOR",
                PublicUse=True,
                StartDate=date(2024, 1, 1),
                Lines=[TXCLine(id="LINE:FLX002", LineName="FLX002")],
                FlexibleService=TXCFlexibleService(
                    Origin="Start",
                    Destination="End",
                    UseAllStopPoints=False,
                    FlexibleJourneyPattern=[
                        TXCFlexibleJourneyPattern(
                            id="jp_1",
                            Direction="outbound",
                            StopPointsInSequence=[],
                            BookingArrangements=TXCBookingArrangements(
                                Description="Phone booking only",
                                Phone=TXCPhone(TelNationalNumber="01234567890"),
                                Email=None,
                                WebAddress=None,
                                AllBookingsTaken=False,
                            ),
                        )
                    ],
                ),
            ),
            TransmodelServiceFactory.create_with_id(
                id_number=3,
                service_code="FLX002",
                service_type="flexible",
            ),
            [
                TransmodelBookingArrangementsFactory.phone_only(
                    service_id=3,
                    description="Phone booking only",
                    phone="01234567890",
                )
            ],
            id="Flexible service with phone-only booking",
        ),
        pytest.param(
            TXCService(
                ServiceCode="FLX003",
                RegisteredOperatorRef="OPERATOR",
                PublicUse=True,
                StartDate=date(2024, 1, 1),
                Lines=[TXCLine(id="LINE:FLX003", LineName="FLX003")],
                FlexibleService=TXCFlexibleService(
                    Origin="Start",
                    Destination="End",
                    UseAllStopPoints=False,
                    FlexibleJourneyPattern=[
                        TXCFlexibleJourneyPattern(
                            id="jp_1",
                            Direction="outbound",
                            StopPointsInSequence=[],
                            BookingArrangements=TXCBookingArrangements(
                                Description="Online booking",
                                Phone=None,
                                Email="book@example.com",
                                WebAddress="https://example.com",
                                AllBookingsTaken=False,
                            ),
                        )
                    ],
                ),
            ),
            TransmodelServiceFactory.create_with_id(
                id_number=4,
                service_code="FLX003",
                service_type="flexible",
            ),
            [
                TransmodelBookingArrangementsFactory.online_only(
                    service_id=4,
                    description="Online booking",
                    email="book@example.com",
                    web_address="https://example.com",
                )
            ],
            id="Flexible service with online-only booking",
        ),
        pytest.param(
            TXCService(
                ServiceCode="FLX004",
                RegisteredOperatorRef="OPERATOR",
                PublicUse=True,
                StartDate=date(2024, 1, 1),
                Lines=[TXCLine(id="LINE:FLX004", LineName="FLX004")],
                FlexibleService=TXCFlexibleService(
                    Origin="Start",
                    Destination="End",
                    UseAllStopPoints=False,
                    FlexibleJourneyPattern=[
                        TXCFlexibleJourneyPattern(
                            id="jp_1",
                            Direction="outbound",
                            StopPointsInSequence=[],
                            BookingArrangements=TXCBookingArrangements(
                                Description="Multiple methods",
                                Phone=TXCPhone(TelNationalNumber="01234567890"),
                                Email="book@example.com",
                                WebAddress="https://example.com",
                                AllBookingsTaken=False,
                            ),
                        ),
                        TXCFlexibleJourneyPattern(
                            id="jp_2",
                            Direction="inbound",
                            StopPointsInSequence=[],
                            BookingArrangements=TXCBookingArrangements(
                                Description="Multiple methods",  # Duplicate
                                Phone=TXCPhone(TelNationalNumber="01234567890"),
                                Email="book@example.com",
                                WebAddress="https://example.com",
                                AllBookingsTaken=False,
                            ),
                        ),
                    ],
                ),
            ),
            TransmodelServiceFactory.create_with_id(
                id_number=5,
                service_code="FLX004",
                service_type="flexible",
            ),
            [
                TransmodelBookingArrangementsFactory.all_methods(
                    service_id=5,
                    description="Multiple methods",
                    phone="01234567890",
                    email="book@example.com",
                    web_address="https://example.com",
                )
            ],
            id="Flexible service with multiple booking methods and deduplication",
        ),
    ],
)
def test_create_booking_arrangement(
    txc_service: TXCService,
    transmodel_service: TransmodelService,
    expected_arrangements: list[TransmodelBookingArrangements],
) -> None:
    """
    Test creating booking arrangements from TXC service data.

    """
    result = create_booking_arrangements(txc_service, transmodel_service)

    assert isinstance(result, list)
    assert len(result) == len(expected_arrangements)

    ignore_fields = {"created", "last_updated", "id"}

    fields = {
        key
        for key in TransmodelBookingArrangements.__mapper__.columns.keys()
        if key not in ignore_fields
    }

    for actual, expected in zip(result, expected_arrangements):
        assert isinstance(actual, TransmodelBookingArrangements)
        for field in fields:
            assert getattr(actual, field) == getattr(expected, field)
