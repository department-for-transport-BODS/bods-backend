from io import BytesIO
from unittest.mock import patch

import pytest
from common_layer.exceptions.xml_file_exceptions import (
    DangerousXML,
    FileNotXML,
    XMLSyntaxError,
)
from common_layer.s3 import S3

from timetables_etl.file_validation import (
    FileValidationInputData,
    dangerous_xml_check,
    get_xml_file_object,
    is_xml_file,
    lambda_handler,
    process_file_validation,
)


@pytest.fixture(name="valid_xml_bytesio")
def valid_xml_bytesio():
    """
    Returns a BytesIO object containing valid XML
    """
    xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <child>Some Text</child>
    </root>
    """
    file_obj = BytesIO(xml_content)
    file_obj.name = "valid.xml"
    return file_obj


@pytest.fixture(name="invalid_xml_bytesio")
def invalid_xml_bytesio():
    """
    Returns a BytesIO object containing invalid (unparseable) XML
    """
    xml_content = b"""<root><child>Missing closing tag"""
    file_obj = BytesIO(xml_content)
    file_obj.name = "invalid.xml"
    return file_obj


@pytest.fixture(name="dangerous_xml_bytesio")
def dangerous_xml_bytesio():
    """
    Returns a BytesIO object containing XML that might trigger defusedxml's protections.
    For demonstration, we’ll include a DOCTYPE which is commonly disallowed.
    """
    xml_content = b"""<!DOCTYPE data [ <!ENTITY myent SYSTEM "file:///etc/passwd"> ]>
    <root>&myent;</root>
    """
    file_obj = BytesIO(xml_content)
    file_obj.name = "dangerous.xml"
    return file_obj


def test_dangerous_xml_check_valid(valid_xml_bytesio):
    """
    Test that parsing a valid XML raises no exceptions
    """
    try:
        dangerous_xml_check(valid_xml_bytesio)
    except Exception as e:
        pytest.fail(
            f"dangerous_xml_check should not have raised an exception. Got: {e}"
        )


@patch("timetables_etl.file_validation.log")
def test_dangerous_xml_check_parse_error(mock_log, invalid_xml_bytesio):
    """
    Test that parsing invalid XML raises XMLSyntaxError
    """
    with pytest.raises(XMLSyntaxError):
        dangerous_xml_check(invalid_xml_bytesio)


@patch("timetables_etl.file_validation.log")
def test_dangerous_xml_check_dangerous_xml(mock_log, dangerous_xml_bytesio):
    """
    Test that parsing an XML with a DOCTYPE or other dangerous constructs
    raises DangerousXML
    """
    with pytest.raises(DangerousXML):
        dangerous_xml_check(dangerous_xml_bytesio)


@patch.object(S3, "download_fileobj")
def test_get_xml_file_object(mock_download, valid_xml_bytesio):
    """
    Test that get_xml_file_object returns a BytesIO object
    from the S3 download
    """
    mock_download.return_value = valid_xml_bytesio
    result = get_xml_file_object("fake-bucket", "fake-key")

    assert isinstance(result, BytesIO)
    assert b"<root>" in result.getvalue()  # check that content is correct
    mock_download.assert_called_once_with("fake-key")


@patch("timetables_etl.file_validation.get_xml_file_object")
def test_process_file_validation_success(mock_get_xml_file_object, valid_xml_bytesio):
    """
    Test that process_file_validation returns True when valid
    """
    mock_get_xml_file_object.return_value = valid_xml_bytesio
    input_data = FileValidationInputData(
        DatasetRevisionId=1, Bucket="fake-bucket", ObjectKey="fake-key.xml"
    )

    process_file_validation(input_data)
    mock_get_xml_file_object.assert_called_once_with("fake-bucket", "fake-key.xml")


@patch("timetables_etl.file_validation.get_xml_file_object")
@patch("timetables_etl.file_validation.log")
def test_process_file_validation_failure(
    mock_log, mock_get_xml_file_object, invalid_xml_bytesio
):
    """
    Test that process_file_validation raises an exception for invalid XML
    """

    mock_get_xml_file_object.return_value = invalid_xml_bytesio
    input_data = FileValidationInputData(
        DatasetRevisionId=1, Bucket="fake-bucket", ObjectKey="fake-key.xml"
    )

    with pytest.raises(XMLSyntaxError):
        process_file_validation(input_data)


@patch("timetables_etl.file_validation.process_file_validation")
def test_lambda_handler_success(mock_process, caplog):
    """
    Test that lambda_handler returns a success response
    """
    mock_process.return_value = True
    event = {"DatasetRevisionId": 1, "Bucket": "fake-bucket", "ObjectKey": "fake-key"}

    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    assert "Completed File Validation" in response["body"]
    mock_process.assert_called_once()


@patch(
    "timetables_etl.file_validation.process_file_validation",
    side_effect=XMLSyntaxError("test.xml", "parse error"),  # type: ignore
)
def test_lambda_handler_failure(mock_process, caplog):
    """
    Test that lambda_handler raises an exception when process_file_validation fails
    """
    event = {"DatasetRevisionId": 1, "Bucket": "fake-bucket", "ObjectKey": "fake-key"}

    with pytest.raises(XMLSyntaxError):
        lambda_handler(event, None)
    mock_process.assert_called_once()


def test_valid_xml_filename():
    for filename in ["example.xml", "example.XML"]:
        assert is_xml_file(filename) == True


def test_invalid_filename_failure():
    for filename in ["example", "example.txt", ""]:
        # Should raise InvalidFileFormatError
        with pytest.raises(FileNotXML) as context:
            is_xml_file(filename)
            assert "FILE_NOT_XML_ERROR" in str(context.value) is True
