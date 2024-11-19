from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from freezegun import freeze_time
from pti.validators.txc_revision import TXCRevisionValidator


@patch("pti.validators.txc_revision.DatasetRepository")
@patch("pti.validators.txc_revision.DatasetRevisionRepository")
@patch("pti.validators.txc_revision.TxcFileAttributesRepository")
def test_revision_get_by_service_code_and_lines(m_file_attributes_repo, m_dataset_revision_repo, m_dataset_repo):
    """
    GIVEN a DatasetRevision with two TXCFileAttributes with the same service_code and
    lines.
    WHEN `get_live_attribute_by_service_code` is called.
    THEN a list of TXCFileAttributes are returned ordered in ascending order by
    revision_number
    """
    live_revision_id = 123
    m_revision = MagicMock(upload_file=None, dataset_id=234)
    m_dataset_repo.return_value.get_by_id.return_value = MagicMock(id=234, live_revision_id=live_revision_id)
    m_dataset_revision_repo.return_value.get_by_id.return_value = MagicMock(id=live_revision_id)

    service_code = "ABC"
    lines = ["1", "2"]

    m_txc_file_attributes_1 = MagicMock(
        revision=m_revision,
        service_code=service_code,
        revision_number=0,
        line_names=lines,
    )
    m_txc_file_attributes_2 = MagicMock(
        revision=m_revision,
        service_code=service_code,
        revision_number=2,
        line_names=lines,
    )
    m_txc_file_attributes_3 = MagicMock(
        revision=m_revision,
        service_code=service_code,
        revision_number=2,
    )

    # TXCFileAttributes returned without sorting or filtering
    m_file_attributes_repo.return_value.get_all.return_value = [
        m_txc_file_attributes_2,
        m_txc_file_attributes_1,
        m_txc_file_attributes_3,
    ]

    # Result should be filtered by line names and service code and sorted by revision number
    expected = [m_txc_file_attributes_1, m_txc_file_attributes_2]

    validator = TXCRevisionValidator(m_revision, txc_file_attributes=MagicMock(), db=MagicMock())
    result = validator.get_live_attributes_by_service_code_and_lines(service_code, lines)

    assert expected == result


@patch("pti.validators.txc_revision.DatasetRepository")
@patch("pti.validators.txc_revision.DatasetRevisionRepository")
@patch("pti.validators.txc_revision.TxcFileAttributesRepository")
def test_filter_by_service_code_and_lines_matches_lines_in_any_order(
    m_file_attributes_repo, m_dataset_revision_repo, m_dataset_repo
):
    """
    GIVEN a DatasetRevision with two TXCFileAttributes with the same service_code and
    lines that are not in order.
    WHEN `get_live_attribute_by_service_code` is called.
    THEN a list of TXCFileAttributes are returned ordered in ascending order by
    revision_number
    """
    live_revision_id = 123
    m_revision = MagicMock(upload_file=None, dataset_id=234)
    m_dataset_repo.return_value.get_by_id.return_value = MagicMock(id=234, live_revision_id=live_revision_id)
    m_dataset_revision_repo.return_value.get_by_id.return_value = MagicMock(id=live_revision_id)
    service_code = "ABC"

    m_txc_file_attributes_1 = MagicMock(
        revision=m_revision,
        service_code=service_code,
        revision_number=0,
        line_names=["1", "2"],
    )
    m_txc_file_attributes_2 = MagicMock(
        revision=m_revision,
        service_code=service_code,
        revision_number=2,
        line_names=["2", "1"],  # Same line names, different order
    )
    m_file_attributes_repo.return_value.get_all.return_value = [m_txc_file_attributes_2, m_txc_file_attributes_1]

    validator = TXCRevisionValidator(m_revision, txc_file_attributes=MagicMock(), db=MagicMock())
    expected = [m_txc_file_attributes_1, m_txc_file_attributes_2]
    actual = validator.get_live_attributes_by_service_code_and_lines(service_code, m_txc_file_attributes_1.line_names)
    assert expected == actual
    actual = validator.get_live_attributes_by_service_code_and_lines(service_code, m_txc_file_attributes_2.line_names)
    assert expected == actual


@patch("pti.validators.txc_revision.DatasetRepository")
@patch("pti.validators.txc_revision.DatasetRevisionRepository")
@patch("pti.validators.txc_revision.TxcFileAttributesRepository")
@pytest.mark.parametrize(
    ("live_number", "draft_number", "modification_datetime_changed", "violation_count"),
    [
        (0, 1, True, 0),
        (2, 2, True, 1),
        (2, 3, True, 0),
        (2, 3, False, 1),
        (2, 1, False, 1),
        (2, 1, True, 1),
    ],
)
def test_revision_number_violation(
    m_file_attributes_repo,
    m_dataset_revision_repo,
    m_dataset_repo,
    live_number,
    draft_number,
    modification_datetime_changed,
    violation_count,
):
    """
    Given a Dataset with live revision and a draft revision

    When the modification_datetime has changed and revision_number has not
    Then a violation is generated

    When the modification_datetime has changed and revision_number has
    been decremented
    Then a violation is generated

    When the modification_datetime is unchanged between revisions
    Then no violation is generated regardless of the revision_number
    """
    live_revision_id = 123
    dataset = MagicMock(id=234, live_revision_id=live_revision_id)

    live_revision = MagicMock(id=live_revision_id, upload_file=None, is_published=True)
    draft_revision = MagicMock(dataset_id=dataset.id, upload_file=None, is_published=False)

    m_dataset_repo.return_value.get_by_id.return_value = dataset
    m_dataset_revision_repo.return_value.get_by_id.return_value = live_revision

    with freeze_time("2024-01-05 10:30:00"):
        now = datetime.now()
        if modification_datetime_changed:
            live_modification_datetime = now - timedelta(days=1)
            draft_modification_datetime = now
        else:
            live_modification_datetime = now
            draft_modification_datetime = now

        service_code = "ABC"

        live_revision_file_attributes = MagicMock(
            filename="filename1.xml",
            revision_id=live_revision.id,
            service_code=service_code,
            revision_number=live_number,
            modification_datetime=live_modification_datetime,
        )
        draft_file_attributes = MagicMock(
            filename="filename2.xml",
            revision=draft_revision,
            service_code=service_code,
            revision_number=draft_number,
            modification_datetime=draft_modification_datetime,
        )
        m_file_attributes_repo.return_value.get_all.return_value = [live_revision_file_attributes]

        validator = TXCRevisionValidator(draft_revision, draft_file_attributes, MagicMock())
        validator.validate_revision_number()
        assert len(validator.violations) == violation_count


@patch("pti.validators.txc_revision.DatasetRepository")
@patch("pti.validators.txc_revision.DatasetRevisionRepository")
@patch("pti.validators.txc_revision.TxcFileAttributesRepository")
@pytest.mark.parametrize(
    (
        "live_number",
        "draft_number",
        "live_lines",
        "draft_lines",
        "violation_count",
    ),
    [
        (0, 1, ["line1", "line2"], ["line1", "line2"], 0),
        (2, 2, ["line1", "line2"], ["line1", "line2"], 1),
        (2, 3, ["line1", "line2"], ["line2", "line1"], 0),
        (2, 1, ["line1", "line2"], ["line1", "line2"], 1),
        (2, 1, ["line1", "line2"], ["line2", "line1"], 1),
        (1, 2, ["34"], ["34"], 0),
        (1, 1, ["33"], ["34"], 0),
    ],
)
def test_revision_number_service_and_line_violation(
    m_file_attributes_repo,
    m_dataset_revision_repo,
    m_dataset_repo,
    live_number,
    draft_number,
    live_lines,
    draft_lines,
    violation_count,
):
    """
    Given a Dataset with live revision and a draft revision

    When the lines match and revision_number has been decremented
    Then a violation is generated

    When the lines dont match and revision_number has been decremented
    Then a violation is not generated

    When the lines match and revision_number has been incremented
    Then a violation is not generated

    """
    dataset = MagicMock(id=234, live_revision_id=123)

    live_revision = MagicMock(id=123, upload_file=None, is_published=True)
    draft_revision = MagicMock(dataset_id=dataset, upload_file=None, is_published=False)

    m_dataset_repo.return_value.get_by_id.return_value = dataset
    m_dataset_revision_repo.return_value.get_by_id.return_value = live_revision

    with freeze_time("2024-01-05 10:30:00"):
        now = datetime.now()
        live_modification_datetime = now - timedelta(days=1)
        draft_modification_datetime = now

        service_code = "ABC"
        live_revision_file_attributes = MagicMock(
            filename="filename1.xml",
            revision=live_revision,
            service_code=service_code,
            revision_number=live_number,
            line_names=live_lines,
            modification_datetime=live_modification_datetime,
        )
        draft_file_attributes = MagicMock(
            filename="filename2.xml",
            revision=draft_revision,
            service_code=service_code,
            revision_number=draft_number,
            modification_datetime=draft_modification_datetime,
            line_names=draft_lines,
        )
        m_file_attributes_repo.return_value.get_all.return_value = [live_revision_file_attributes]

        validator = TXCRevisionValidator(draft_revision, draft_file_attributes, MagicMock())
        validator.validate_revision_number()
        assert len(validator.violations) == violation_count
