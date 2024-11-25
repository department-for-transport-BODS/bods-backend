"""
Test Createing transmodel_service rows
"""

from datetime import date
from typing import Callable

import pytest

from timetables_etl.etl.app.database.models.model_organisation import (
    OrganisationDatasetRevision,
    OrganisationTXCFileAttributes,
)
from timetables_etl.etl.app.database.models.model_transmodel import TransmodelService
from timetables_etl.etl.app.transform.services import make_transmodel_service
from timetables_etl.etl.app.txc.models.txc_service import (
    TXCLine,
    TXCLineDescription,
    TXCService,
    TXCStandardService,
)
from timetables_etl.etl.app.txc.models.txc_service_flexible import (
    TXCBookingArrangements,
    TXCFixedStopUsage,
    TXCFlexibleJourneyPattern,
    TXCFlexibleService,
    TXCFlexibleStopUsage,
    TXCPhone,
)


def get_revision_id(request: pytest.FixtureRequest) -> int:
    """Get revision ID from fixture"""
    return request.getfixturevalue("organisation_dataset_revision").id


def get_file_attrs_id(request: pytest.FixtureRequest) -> int:
    """Get file attributes ID from fixture"""
    return request.getfixturevalue("organisation_txc_file_attributes").id


@pytest.mark.parametrize(
    "service,expected_result",
    [
        pytest.param(
            TXCService(
                RevisionNumber=1,
                ServiceCode="UZ000FLIX:UK045",
                PrivateCode="UK045",
                RegisteredOperatorRef="FLIX",
                PublicUse=True,
                StartDate=date(2024, 11, 11),
                EndDate=date(2025, 1, 5),
                StandardService=TXCStandardService(
                    Origin="London",
                    Destination="Plymouth",
                    JourneyPattern=[],
                ),
                FlexibleService=None,
                Lines=[
                    TXCLine(
                        id="FLIX:UZ000FLIX:UK045:UK045",
                        LineName="UK045",
                        MarketingName=None,
                        OutboundDescription=TXCLineDescription(
                            Origin="London",
                            Destination="Plymouth",
                            Description="London - Plymouth",
                        ),
                        InboundDescription=TXCLineDescription(
                            Origin="Plymouth",
                            Destination="London",
                            Description="Plymouth - London",
                        ),
                    )
                ],
                Mode="coach",
            ),
            lambda r: TransmodelService(
                service_code="UZ000FLIX:UK045",
                name="UK045",
                other_names=[],
                start_date=date(2024, 11, 11),
                service_type="standard",
                end_date=date(2025, 1, 5),
                revision_id=get_revision_id(r),
                txcfileattributes_id=get_file_attrs_id(r),
            ),
            id="Standard Service",
        ),
        pytest.param(
            TXCService(
                ServiceCode="PB0002032:467",
                RegisteredOperatorRef="O1",
                PublicUse=True,
                StartDate=date(2022, 1, 1),
                Lines=[TXCLine(id="ARBB:PB0002032:467:53M", LineName="53M")],
                FlexibleService=TXCFlexibleService(
                    Origin="Market Rasen",
                    Destination="Market Rasen",
                    UseAllStopPoints=False,
                    FlexibleJourneyPattern=[
                        TXCFlexibleJourneyPattern(
                            id="jp_1",
                            Direction="outbound",
                            StopPointsInSequence=[
                                TXCFixedStopUsage(
                                    StopPointRef="02903501", TimingStatus="otherPoint"
                                ),
                                TXCFlexibleStopUsage(StopPointRef="02901353"),
                            ],
                            BookingArrangements=TXCBookingArrangements(
                                Description="The booking office is open Monday to Friday 8:30am - 6:30pm",
                                Phone=TXCPhone(TelNationalNumber="0000 000 0000"),
                                Email="example@example.com",
                                WebAddress="https://example.com/",
                                AllBookingsTaken=True,
                            ),
                        )
                    ],
                ),
            ),
            lambda r: TransmodelService(
                service_code="PB0002032:467",
                name="53M",
                other_names=[],
                start_date=date(2022, 1, 1),
                end_date=None,
                service_type="flexible",
                revision_id=get_revision_id(r),
                txcfileattributes_id=get_file_attrs_id(r),
            ),
            id="Flexible Service",
        ),
    ],
)
def test_make_transmodel_service(
    request: pytest.FixtureRequest,
    service: TXCService,
    expected_result: Callable[[pytest.FixtureRequest], TransmodelService],
    organisation_dataset_revision: OrganisationDatasetRevision,
    organisation_txc_file_attributes: OrganisationTXCFileAttributes,
):
    """
    Test converting a TXCService to DB row Data for transmodel_service
    """
    result = make_transmodel_service(
        service,
        organisation_dataset_revision,
        organisation_txc_file_attributes,
    )
    expected = expected_result(request)
    assert isinstance(result, TransmodelService)
    assert result == expected
