"""
Tests for Schema Check logic
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from common_layer.exceptions import ETLException, SchemaMismatch, SchemaUnknown
from freezegun import freeze_time
from lxml import etree
from lxml.etree import _LogEntry  # type: ignore

from common_lambdas.schema_check.app.constants import XMLDataType, XMLSchemaType
from common_lambdas.schema_check.app.schema_check import (
    create_violation_from_error,
    create_violation_from_parse_error,
    get_schema_violations,
    process_schema_check,
    validate_schema_type,
)

REVISION_ID: int = 123


@pytest.mark.parametrize(
    "error_params,expected_result",
    [
        pytest.param(
            {
                "filename": "test.xml",
                "line": 42,
                "message": "Invalid element found",
            },
            {
                "filename": "test.xml",
                "line": 42,
                "details": "Invalid element found",
            },
            id="Simple XML File",
        ),
        pytest.param(
            {
                "filename": "/path/to/some/file.xml",
                "line": 10,
                "message": "Missing required attribute",
            },
            {
                "filename": "file.xml",
                "line": 10,
                "details": "Missing required attribute",
            },
            id="Unix Path With Multiple Directories",
        ),
        pytest.param(
            {
                "filename": "data.xml",
                "line": 100,
                "message": "Element 'Journey': This element is not expected. Expected is one of ( PrivateCode, Direction ).",
            },
            {
                "filename": "data.xml",
                "line": 100,
                "details": "Element 'Journey': This element is not expected. Expected is one of ( PrivateCode, Direction ).",
            },
            id="Complex Schema Validation Error Message",
        ),
    ],
)
@freeze_time("2024-01-03 12:00:00")
def test_create_violation_from_error(
    error_params: dict[str, str | int], expected_result: dict[str, str | int]
):
    """
    Test creation of DataQualitySchemaViolation from different lxml error scenarios
    """
    frozen_time = datetime(2024, 1, 3, 12, 0, 0, tzinfo=UTC)
    filename = "filename.xml"

    mock_error = Mock(spec=_LogEntry)
    mock_error.filename = error_params["filename"]
    mock_error.line = error_params["line"]
    mock_error.message = error_params["message"]

    violation = create_violation_from_error(mock_error, REVISION_ID, filename)

    assert violation.filename == filename
    assert violation.line == expected_result["line"]
    assert violation.details == expected_result["details"]
    assert violation.revision_id == REVISION_ID
    assert violation.created == frozen_time


# Constants for test data
BASIC_SCHEMA = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="person">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="name" type="xs:string"/>
                <xs:element name="age" type="xs:integer"/>
            </xs:sequence>
        </xs:complexType>
    </xs:element>
</xs:schema>"""


@pytest.fixture(name="schema")
def schema_fixture() -> etree.XMLSchema:
    """Fixture to provide parsed XML schema"""
    schema_doc = etree.fromstring(BASIC_SCHEMA.encode())
    return etree.XMLSchema(schema_doc)


@pytest.mark.parametrize(
    "test_xml,expected_violations",
    [
        pytest.param(
            """<?xml version="1.0" encoding="UTF-8"?>
            <person>
                <name>John Doe</name>
                <age>25</age>
            </person>""",
            [],
            id="valid_xml",
        ),
    ],
)
@freeze_time("2024-01-03 12:00:00")
def test_schema_validation(
    schema: etree.XMLSchema, test_xml: str, expected_violations: list[dict[str, str]]
):
    """
    Test schema validation with various XML inputs

    """
    # Given
    xml_doc = etree.fromstring(test_xml.encode())
    frozen_time = datetime(2024, 1, 3, 12, 0, 0, tzinfo=UTC)
    filename = "filename.xml"

    # When
    violations = get_schema_violations(schema, xml_doc, REVISION_ID, filename=filename)

    # Then
    assert len(violations) == len(expected_violations)

    for violation, expected in zip(violations, expected_violations):
        assert violation.filename == filename
        assert violation.line == expected["line"]
        assert violation.details == expected["details"]
        assert violation.revision_id == REVISION_ID
        assert violation.created == frozen_time


@pytest.mark.parametrize(
    "data_type,detected_schema_type,expected_result",
    [
        pytest.param(
            XMLDataType.TIMETABLES,
            XMLSchemaType.TRANSXCHANGE,
            None,
            id="Valid Timetables Schema",
        ),
        pytest.param(
            XMLDataType.TIMETABLES,
            XMLSchemaType.NETEX,
            SchemaMismatch,
            id="Invalid Timetables Schema: NeTEx for Timetables not supported",
        ),
        pytest.param(
            XMLDataType.FARES,
            XMLSchemaType.NETEX,
            None,
            id="Valid Fares Schema",
        ),
        pytest.param(
            XMLDataType.FARES,
            XMLSchemaType.TRANSXCHANGE,
            SchemaMismatch,
            id="Invalid Fares Schema: TransXChange for Fares not supported",
        ),
        pytest.param(
            "UNKNOWN_TYPE",
            XMLSchemaType.TRANSXCHANGE,
            SchemaUnknown,
            id="Unknown data type",
        ),
    ],
)
def test_validate_schema_type(
    data_type: XMLDataType,
    detected_schema_type: XMLSchemaType,
    expected_result: None | type[ETLException],
) -> None:
    """
    Test schema type validation

    Args:
        data_type: The data type being validated
        detected_schema_type: The schema type detected in the XML file
        expected_result: None if validation should pass, or the expected exception type
    """
    if expected_result is None:
        validate_schema_type(data_type, detected_schema_type)
    else:
        with pytest.raises(expected_result):
            validate_schema_type(data_type, detected_schema_type)


@pytest.mark.parametrize(
    "exc_params,expected_result",
    [
        pytest.param(
            {
                "lineno": 42,
                "msg": "Start tag expected, '<' not found, line 42, column 5",
            },
            {
                "line": 42,
                "details": "Start tag expected, '<' not found, line 42, column 5",
            },
            id="XMLSyntaxError with lineno and msg",
        ),
        pytest.param(
            {
                "lineno": None,
                "msg": "Malformed XML",
            },
            {
                "line": 0,
                "details": "Malformed XML",
            },
            id="Exception with None lineno defaults to 0",
        ),
        pytest.param(
            {
                "no_lineno": True,
                "no_msg": True,
            },
            {
                "line": 0,
                "details": "Test exception without attributes",
            },
            id="Exception without lineno or msg attributes uses defaults",
        ),
    ],
)
@freeze_time("2024-01-03 12:00:00")
def test_create_violation_from_parse_error(
    exc_params: dict, expected_result: dict[str, str | int]
):
    """
    Test creation of DataQualitySchemaViolation from parse errors with defensive fallbacks
    """
    frozen_time = datetime(2024, 1, 3, 12, 0, 0, tzinfo=UTC)
    filename = "malformed.xml"

    # Create mock exception with optional attributes
    mock_exc = MagicMock()
    if "lineno" in exc_params:
        mock_exc.lineno = exc_params["lineno"]
    if "msg" in exc_params:
        mock_exc.msg = exc_params["msg"]
    if exc_params.get("no_lineno") or exc_params.get("no_msg"):
        # For the case with no attributes, set a string representation
        mock_exc.__str__.return_value = "Test exception without attributes"

    violation = create_violation_from_parse_error(mock_exc, REVISION_ID, filename)

    assert violation.filename == filename
    assert violation.line == expected_result["line"]
    assert violation.details == expected_result["details"]
    assert violation.revision_id == REVISION_ID
    assert violation.created == frozen_time


@freeze_time("2024-01-03 12:00:00")
def test_process_schema_check_with_parse_error():
    """
    Test that process_schema_check catches parse errors and creates a violation row
    """
    # Given
    input_data = Mock()
    input_data.s3_file_key = "uploads/file.xml"
    input_data.revision_id = REVISION_ID

    frozen_time = datetime(2024, 1, 3, 12, 0, 0, tzinfo=UTC)
    filename = "file.xml"

    # Create an exception that mimics XMLSyntaxError
    parse_error = Exception("Start tag expected, '<' not found")
    parse_error.lineno = 15
    parse_error.msg = "Start tag expected, '<' not found"

    with patch(
        "common_lambdas.schema_check.app.schema_check.get_filename_from_object_key_except",
        return_value=filename,
    ):
        with patch(
            "common_lambdas.schema_check.app.schema_check.parse_xml_from_s3",
            side_effect=parse_error,
        ):
            # When
            violations = process_schema_check(input_data)

            # Then
            assert len(violations) == 1
            violation = violations[0]
            assert violation.filename == filename
            assert violation.line == 15
            assert violation.details == "Start tag expected, '<' not found"
            assert violation.revision_id == REVISION_ID
            assert violation.created == frozen_time

