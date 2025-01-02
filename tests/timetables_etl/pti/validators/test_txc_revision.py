from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from freezegun import freeze_time
from pti.validators.txc_revision import TXCRevisionValidator


def test_revision_get_by_service_code_and_lines():
    """
    GIVEN a DatasetRevision with two TXCFileAttributes with the same service_code and
    lines.
    WHEN `get_live_attribute_by_service_code` is called.
    THEN a list of TXCFileAttributes are returned ordered in ascending order by
    revision_number
    """
    live_revision_id = 123

    service_code = "ABC"
    lines = ["1", "2"]

    txc_file_attributes_1 = MagicMock(
        service_code=service_code,
        revision_number=0,
        line_names=lines,
    )
    txc_file_attributes_2 = MagicMock(
        service_code=service_code,
        revision_number=2,
        line_names=lines,
    )
    txc_file_attributes_3 = MagicMock(
        service_code=service_code,
        revision_number=2,
    )

    # TXCFileAttributes without sorting or filtering
    live_txc_file_attributes = [
        txc_file_attributes_2,
        txc_file_attributes_1,
        txc_file_attributes_3,
    ]

    # Result should be filtered by line names and service code and sorted by revision number
    expected = [txc_file_attributes_1, txc_file_attributes_2]

    validator = TXCRevisionValidator(
        txc_file_attributes=MagicMock(),
        live_txc_file_attributes=live_txc_file_attributes,
    )
    result = validator.get_live_attributes_by_service_code_and_lines(
        service_code, lines
    )

    assert expected == result


def test_filter_by_service_code_and_lines_matches_lines_in_any_order():
    """
    GIVEN a DatasetRevision with two TXCFileAttributes with the same service_code and
    lines that are not in order.
    WHEN `get_live_attribute_by_service_code` is called.
    THEN a list of TXCFileAttributes are returned ordered in ascending order by
    revision_number
    """
    service_code = "ABC"

    txc_file_attributes_1 = MagicMock(
        service_code=service_code,
        revision_number=0,
        line_names=["1", "2"],
    )
    txc_file_attributes_2 = MagicMock(
        service_code=service_code,
        revision_number=2,
        line_names=["2", "1"],  # Same line names, different order
    )
    live_txc_file_attributes = [txc_file_attributes_2, txc_file_attributes_1]

    validator = TXCRevisionValidator(
        txc_file_attributes=MagicMock(),
        live_txc_file_attributes=live_txc_file_attributes,
    )
    expected = [txc_file_attributes_1, txc_file_attributes_2]
    actual = validator.get_live_attributes_by_service_code_and_lines(
        service_code, txc_file_attributes_1.line_names
    )
    assert expected == actual
    actual = validator.get_live_attributes_by_service_code_and_lines(
        service_code, txc_file_attributes_2.line_names
    )
    assert expected == actual


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
    draft_revision = MagicMock(
        dataset_id=dataset.id, upload_file=None, is_published=False
    )

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

        validator = TXCRevisionValidator(
            txc_file_attributes=draft_file_attributes,
            live_txc_file_attributes=[live_revision_file_attributes],
        )
        violations = validator.get_violations()
        assert len(violations) == violation_count


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

        validator = TXCRevisionValidator(
            draft_file_attributes,
            live_txc_file_attributes=[live_revision_file_attributes],
        )
        violations = validator.get_violations()
        assert len(violations) == violation_count
