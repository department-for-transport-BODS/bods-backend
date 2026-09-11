"""Tests for the file validation handler."""

from unittest.mock import Mock, patch

from common_layer.exceptions import XMLSyntaxError
from file_validation.app.db_operations import add_violations_to_db
from file_validation.app.file_validation import handle_xml_syntax_error
from file_validation.app.models import FileValidationInputData


def test_handle_xml_syntax_error_inserts_violation() -> None:
    """A syntax error is converted to one database violation."""
    input_data = FileValidationInputData(
        DatasetRevisionId=123,
        Bucket="test-bucket",
        ObjectKey="timetables/invalid.xml",
    )
    error = XMLSyntaxError("Invalid XML")
    db = Mock()

    with (
        patch("file_validation.app.file_validation.SqlDB", return_value=db),
        patch(
            "file_validation.app.file_validation.add_violations_to_db"
        ) as add_violations,
    ):
        handle_xml_syntax_error(error, input_data)

    add_violations.assert_called_once()
    called_db, violations = add_violations.call_args.args
    assert called_db is db
    assert len(violations) == 1
    assert violations[0].filename == "invalid.xml"
    assert violations[0].revision_id == 123
    assert "Invalid XML" in violations[0].details


def test_add_violations_to_db_bulk_inserts_violations() -> None:
    """Violations are inserted through the schema violation repository."""
    db = Mock()
    violation = Mock()
    inserted = [Mock()]

    with patch(
        "file_validation.app.db_operations.DataQualitySchemaViolationRepo"
    ) as repo_type:
        repo_type.return_value.bulk_insert.return_value = inserted
        result = add_violations_to_db(db, [violation])

    repo_type.assert_called_once_with(db)
    repo_type.return_value.bulk_insert.assert_called_once_with([violation])
    assert result == inserted
