"""
Test Createing transmodel_service rows
"""

from datetime import date
from typing import Callable

import pytest
from common_layer.database.models import TransmodelService
from common_layer.xml.txc.models import TXCService

from tests.factories.database.organisation import (
    OrganisationDatasetRevisionFactory,
    OrganisationTXCFileAttributesFactory,
)
from tests.timetables_etl.factories.txc import TXCServiceFactory
from timetables_etl.etl.app.transform.services import make_transmodel_service


@pytest.mark.parametrize(
    "service,superceded_timetable,expected_service",
    [
        pytest.param(
            TXCServiceFactory.create(with_standard_line=True),
            False,
            lambda revision_id, file_attrs_id: TransmodelService(
                service_code="UZ000FLIX:UK045",
                name="UK045",
                other_names=[],
                start_date=date(2024, 11, 11),
                service_type="standard",
                end_date=date(2025, 1, 5),
                revision_id=revision_id,
                txcfileattributes_id=file_attrs_id,
            ),
            id="Standard Service",
        ),
        pytest.param(
            TXCServiceFactory.create(flexible=True),
            False,
            lambda revision_id, file_attrs_id: TransmodelService(
                service_code="PB0002032:467",
                name="53M",
                other_names=[],
                start_date=date(2022, 1, 1),
                end_date=None,
                service_type="flexible",
                revision_id=revision_id,
                txcfileattributes_id=file_attrs_id,
            ),
            id="Flexible Service",
        ),
        pytest.param(
            TXCServiceFactory.create(flexible=True),
            True,
            lambda revision_id, file_attrs_id: TransmodelService(
                service_code="PB0002032:467",
                name="53M",
                other_names=[],
                start_date=date(2022, 1, 1),
                end_date=None,
                service_type="flexible",
                revision_id=revision_id,
                txcfileattributes_id=None,
            ),
            id="Flexible Service",
        ),
    ],
)
def test_make_transmodel_service(
    service: TXCService,
    superceded_timetable: bool,
    expected_service: Callable[[int, int], TransmodelService],
) -> None:
    """
    Test converting a TXCService to DB row Data for transmodel_service
    Fixed IDs for revision and file attrs since we don't care about them
    """
    org_revision = OrganisationDatasetRevisionFactory.create_with_id(1234)
    org_file_attrs = OrganisationTXCFileAttributesFactory.create_with_id(5678)

    result = make_transmodel_service(
        service, org_revision, org_file_attrs, superceded_timetable
    )
    expected = expected_service(org_revision.id, org_file_attrs.id)

    assert isinstance(result, TransmodelService)
    assert result == expected
