from datetime import date, datetime, timedelta

from common_layer.database.client import SqlDB
from common_layer.database.dataclasses import ServiceStats
from common_layer.database.repos import TransmodelServiceRepo

from tests.factories.database import TransmodelServiceFactory


def test_service_repo_get_service_stats_by_revision_id(test_db: SqlDB):

    revision_id = 123
    repo = TransmodelServiceRepo(test_db)

    result = repo.get_service_stats_by_revision_id(revision_id)

    # No services in DB
    assert result == ServiceStats(
        first_service_start=None,
        first_expiring_service=None,
        last_expiring_service=None,
    )

    # Create services
    earliest_start_date = date(2024, 12, 1)
    earliest_end_date = date(2025, 1, 10)
    latest_end_date = date(2025, 1, 13)

    earliest_starting_service = TransmodelServiceFactory.create(
        start_date=earliest_start_date,
        end_date=datetime(2025, 1, 11),
        revision_id=revision_id,
    )
    first_expiring_service = TransmodelServiceFactory.create(
        start_date=datetime(2025, 1, 1),
        end_date=earliest_end_date,
        revision_id=revision_id,
    )
    last_expiring_service = TransmodelServiceFactory.create(
        start_date=datetime(2025, 2, 1),
        end_date=latest_end_date,
        revision_id=revision_id,
    )
    unrelated_service = TransmodelServiceFactory.create(
        start_date=datetime(2025, 2, 1),
        end_date=latest_end_date + timedelta(days=1),
        revision_id=321,
    )

    with test_db.session_scope() as session:
        session.add_all(
            [
                earliest_starting_service,
                first_expiring_service,
                last_expiring_service,
                unrelated_service,
            ]
        )
        session.commit()

    result = repo.get_service_stats_by_revision_id(revision_id)
    assert result == ServiceStats(
        first_service_start=earliest_start_date,
        first_expiring_service=earliest_end_date,
        last_expiring_service=latest_end_date,
    )
