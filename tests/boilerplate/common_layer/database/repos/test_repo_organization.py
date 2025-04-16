from datetime import datetime, timedelta, timezone

import pytest
from common_layer.database.client import SqlDB
from common_layer.database.dataclasses import RevisionStats, TXCFileStats
from common_layer.database.models.model_organisation import OrganisationDatasetRevision
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo,
    OrganisationTXCFileAttributesRepo,
)
from common_layer.enums import FeedStatus
from freezegun import freeze_time
from pytz import UTC

from tests.factories.database import OrganisationTXCFileAttributesFactory
from tests.factories.database.organisation import OrganisationDatasetRevisionFactory


@pytest.mark.parametrize(
    "initial_state,expected_state",
    [
        pytest.param(
            {"is_published": False, "status": FeedStatus.SUCCESS, "published_at": None},
            {
                "is_published": True,
                "status": FeedStatus.LIVE,
            },
            id="Successfully publish",
        ),
        pytest.param(
            {
                "is_published": True,
                "status": FeedStatus.LIVE,
                "published_at": datetime(2025, 1, 2, tzinfo=UTC),
            },
            {
                "is_published": True,
                "status": FeedStatus.LIVE,
                "published_at": datetime(2025, 1, 2, tzinfo=UTC),
            },
            id="Already published, no updates",
        ),
        pytest.param(
            {
                "is_published": False,
                "status": FeedStatus.ERROR,
                "published_at": None,
            },
            {
                "is_published": False,
                "status": FeedStatus.ERROR,
                "published_at": None,
            },
            id="Revision not in success state, no updates",
        ),
    ],
)
def test_dataset_revision_publish_revision_success(
    test_db, initial_state, expected_state
):

    revision = OrganisationDatasetRevisionFactory(**initial_state)

    with test_db.session_scope() as session:
        session.add(revision)
        session.flush()
        session.expunge(revision)

    now = datetime.now(UTC)
    if (
        initial_state["is_published"] is False
        and expected_state["is_published"] is True
    ):
        expected_state["published_at"] = now

    with freeze_time(now):
        repo = OrganisationDatasetRevisionRepo(test_db)
        repo.publish_revision(revision.id)

    with test_db.session_scope() as session:
        record_after_update = (
            session.query(OrganisationDatasetRevision)
            .filter_by(id=revision.id)
            .one_or_none()
        )
        for attr, expected_value in expected_state.items():
            assert getattr(record_after_update, attr) == expected_value


def test_dataset_revision_update_stats(test_db):
    repo = OrganisationDatasetRevisionRepo(test_db)
    revision = OrganisationDatasetRevisionFactory.create(
        publisher_creation_datetime=None,
        publisher_modified_datetime=None,
        first_expiring_service=None,
        last_expiring_service=None,
    )

    with test_db.session_scope() as session:
        session.add(revision)
        session.flush()
        session.expunge(revision)

    assert revision.id is not None

    stats = RevisionStats(
        publisher_creation_datetime=datetime(2024, 12, 1, tzinfo=timezone.utc),
        publisher_modification_datetime=datetime(2025, 2, 1, tzinfo=timezone.utc),
        first_expiring_service=datetime(2026, 2, 3, tzinfo=timezone.utc),
        last_expiring_service=datetime(2027, 1, 5, tzinfo=timezone.utc),
        first_service_start=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    repo.update_stats(revision.id, stats)

    updated_revision = repo.get_by_id(revision.id)
    assert updated_revision is not None

    assert (
        updated_revision.publisher_creation_datetime
        == stats.publisher_creation_datetime
    )
    assert (
        updated_revision.publisher_modified_datetime
        == stats.publisher_modification_datetime
    )
    assert updated_revision.first_expiring_service == stats.first_expiring_service
    assert updated_revision.last_expiring_service == stats.last_expiring_service
    assert updated_revision.first_service_start == stats.first_service_start


def test_txc_file_attributes_get_file_datetime_stats_by_revision_id(test_db: SqlDB):

    revision_id = 123
    repo = OrganisationTXCFileAttributesRepo(test_db)

    # No file attributes in DB
    result = repo.get_file_datetime_stats_by_revision_id(revision_id)
    assert result == TXCFileStats(
        first_creation_datetime=None, last_modification_datetime=None
    )

    # Create file attributes
    earliest_txc_creation_date = datetime(2024, 12, 1, tzinfo=timezone.utc)
    latest_txc_modification_date = datetime(2025, 1, 10, tzinfo=timezone.utc)

    earliest_created_txc = OrganisationTXCFileAttributesFactory.create(
        creation_datetime=earliest_txc_creation_date,
        modification_datetime=datetime(2024, 12, 2),
        revision_id=revision_id,
    )
    latest_modified_txc = OrganisationTXCFileAttributesFactory.create(
        creation_datetime=datetime(2024, 12, 2),
        modification_datetime=latest_txc_modification_date,
        revision_id=revision_id,
    )
    unrelated_txc = OrganisationTXCFileAttributesFactory.create(
        creation_datetime=datetime(2024, 12, 2),
        modification_datetime=latest_txc_modification_date + timedelta(days=1),
        revision_id=321,
    )

    with test_db.session_scope() as session:
        session.add_all([earliest_created_txc, latest_modified_txc, unrelated_txc])
        session.commit()

    result = repo.get_file_datetime_stats_by_revision_id(revision_id)
    assert result == TXCFileStats(
        first_creation_datetime=earliest_txc_creation_date,
        last_modification_datetime=latest_txc_modification_date,
    )
