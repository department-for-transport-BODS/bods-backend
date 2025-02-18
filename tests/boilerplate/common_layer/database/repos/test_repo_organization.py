from datetime import datetime

import pytest
from common_layer.database.models.model_dqs import DQSTaskResults
from common_layer.database.models.model_organisation import (
    OrganisationDatasetRevision,
    OrganisationTXCFileAttributes,
)
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo,
    OrganisationTXCFileAttributesRepo,
)
from common_layer.enums import FeedStatus
from freezegun import freeze_time
from pytz import UTC

from tests.factories.database.dqs import DQSTaskResultsFactory
from tests.factories.database.organisation import (
    OrganisationDatasetRevisionFactory,
    OrganisationTXCFileAttributesFactory,
)


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


def test_delete_by_revision_id(test_db):
    """
    Test deleting TXCFileAttributes and related DQSTaskResults.
    """

    revision_id = 42

    with test_db.session_scope() as session:
        txc_file_attributes = OrganisationTXCFileAttributesFactory.create_batch(
            3, revision_id=revision_id
        )
        session.add_all(txc_file_attributes)
        session.commit()

        txc_file_attribute_ids = [txc.id for txc in txc_file_attributes]

        # Insert related DQSTaskResults referencing TXCFileAttributes
        dqs_task_results = []
        for txc in txc_file_attributes:
            dqs_task_results.extend(
                DQSTaskResultsFactory.create_batch(
                    2, transmodel_txcfileattributes_id=txc.id
                )
            )

        session.add_all(dqs_task_results)
        session.commit()

    # Check records exist before deletion
    with test_db.session_scope() as session:
        txc_count_before = (
            session.query(OrganisationTXCFileAttributes)
            .filter_by(revision_id=revision_id)
            .count()
        )
        dqs_count_before = (
            session.query(DQSTaskResults)
            .filter(
                DQSTaskResults.transmodel_txcfileattributes_id.in_(
                    txc_file_attribute_ids
                )
            )
            .count()
        )

    assert txc_count_before == 3
    assert dqs_count_before == 6  # 3 TXC attributes x 2 DQS task results each

    # Act
    repo = OrganisationTXCFileAttributesRepo(test_db)
    deleted_count = repo.delete_by_revision_id(revision_id)

    # Check records are deleted
    with test_db.session_scope() as session:
        txc_count_after = (
            session.query(OrganisationTXCFileAttributes)
            .filter_by(revision_id=revision_id)
            .count()
        )
        dqs_count_after = (
            session.query(DQSTaskResults)
            .filter(
                DQSTaskResults.transmodel_txcfileattributes_id.in_(
                    txc_file_attribute_ids
                )
            )
            .count()
        )

    assert deleted_count == 3, "Number of TXCFileAttributes deleted"
    assert txc_count_after == 0
    assert dqs_count_after == 0
