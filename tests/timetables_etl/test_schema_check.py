"""
Tests for the Schema Check ETL
"""

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from freezegun import freeze_time
from lxml import etree
from schema_check.app.app import create_violation_from_error, get_schema_violations


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
def test_create_violation_from_error(error_params, expected_result):
    """
    Test creation of DataQualitySchemaViolation from different lxml error scenarios
    """
    revision_id = 123
    frozen_time = datetime(2024, 1, 3, 12, 0, 0, tzinfo=UTC)

    mock_error = Mock(spec=etree._LogEntry)
    mock_error.filename = error_params["filename"]
    mock_error.line = error_params["line"]
    mock_error.message = error_params["message"]

    violation = create_violation_from_error(mock_error, revision_id)

    assert violation.filename == expected_result["filename"]
    assert violation.line == expected_result["line"]
    assert violation.details == expected_result["details"]
    assert violation.revision_id == revision_id
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


@pytest.fixture
def schema():
    """Fixture to provide parsed XML schema"""
    schema_doc = etree.fromstring(BASIC_SCHEMA.encode())
    return etree.XMLSchema(schema_doc)


@pytest.fixture
def revision_id():
    """Fixture for test revision ID"""
    return 123


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
def test_schema_validation(schema, revision_id, test_xml, expected_violations):
    """
    Test schema validation with various XML inputs

    """
    # Given
    xml_doc = etree.fromstring(test_xml.encode())
    frozen_time = datetime(2024, 1, 3, 12, 0, 0, tzinfo=UTC)

    # When
    violations = get_schema_violations(schema, xml_doc, revision_id)

    # Then
    assert len(violations) == len(expected_violations)

    for violation, expected in zip(violations, expected_violations):
        assert violation.filename == expected["filename"]
        assert violation.line == expected["line"]
        assert violation.details == expected["details"]
        assert violation.revision_id == revision_id
        assert violation.created == frozen_time
