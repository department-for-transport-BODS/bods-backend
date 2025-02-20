from datetime import datetime

import pytest
from common_layer.database.models.model_dqs import DQSReport, DQSTaskResults
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

from tests.factories.database.dqs import DQSReportFactory, DQSTaskResultsFactory
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
    Test deleting TXCFileAttributes by revision id
    Checks that objects and related objects are deleted as expected
    """

    revision_id = 42

    with test_db.session_scope() as session:
        txc_file_attributes = OrganisationTXCFileAttributesFactory.create_batch(
            3, revision_id=revision_id
        )
        session.add_all(txc_file_attributes)
        session.commit()

        # Insert related DQSTaskResults referencing TXCFileAttributes
        # And DQSReport objects referencing the DQSTaskResults
        dqs_task_results = []
        dqs_reports = []
        for txc in txc_file_attributes:
            dqs_report = DQSReportFactory.create(revision_id=revision_id)
            dqs_reports.append(dqs_report)
            task_result = DQSTaskResultsFactory.create(
                transmodel_txcfileattributes=txc, dataquality_report=dqs_report
            )
            dqs_task_results.append(task_result)

        session.add_all(dqs_task_results)
        session.commit()

        dqs_task_result_ids = [task_result.id for task_result in dqs_task_results]
        dqs_report_ids = [report.id for report in dqs_reports]

    # Check records exist before deletion
    with test_db.session_scope() as session:
        txc_count_before = (
            session.query(OrganisationTXCFileAttributes)
            .filter_by(revision_id=revision_id)
            .count()
        )
        dqs_task_result_count_before = (
            session.query(DQSTaskResults)
            .filter(DQSTaskResults.id.in_(dqs_task_result_ids))
            .count()
        )
        dqs_report_count_before = (
            session.query(DQSReport).filter(DQSReport.id.in_(dqs_report_ids)).count()
        )

    assert txc_count_before == 3
    assert dqs_task_result_count_before == 3  # 1 DQS Task per TXCFileAttributes
    assert dqs_report_count_before == 3  # 1 DQS Report per DQS Task

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
        dqs_task_result_count_after = (
            session.query(DQSTaskResults)
            .filter(DQSTaskResults.id.in_(dqs_task_result_ids))
            .count()
        )
        dqs_report_count_after = (
            session.query(DQSReport).filter(DQSReport.id.in_(dqs_report_ids)).count()
        )

    assert deleted_count == 3, "Number of TXCFileAttributes deleted"
    assert txc_count_after == 0
    assert dqs_task_result_count_after == 0
    assert dqs_report_count_after == 0
