from datetime import datetime

import pytest
from common_layer.database.models.model_organisation import OrganisationDatasetRevision
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo,
)
from common_layer.enums import FeedStatus
from freezegun import freeze_time
from pytz import UTC

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
