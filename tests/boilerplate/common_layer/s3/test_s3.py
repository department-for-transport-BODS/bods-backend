"""
S3 Client Unit Tests
"""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from common_layer.s3 import S3


@pytest.fixture
def mock_s3_client():
    with patch("common_layer.s3.client.boto3.client") as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        yield mock_client


@pytest.fixture
def s3_client(mock_s3_client):
    bucket_name = "test_bucket"
    return S3(bucket_name=bucket_name), bucket_name, mock_s3_client


@pytest.fixture
def mock_file_content():
    return b"Test file content"


@pytest.fixture
def test_file_path():
    return "test/path/testfile.txt"


def test_s3_client_local_stack(monkeypatch):
    """Test LocalStack configuration for local environment"""
    monkeypatch.setenv("PROJECT_ENV", "local")
    s3 = S3(bucket_name="test_bucket")
    assert s3._client.meta.endpoint_url == "http://host.docker.internal:4566"


def test_bucket_name(s3_client):
    """Test bucket name property"""
    s3, bucket_name, _ = s3_client
    assert s3.bucket_name == bucket_name


@pytest.mark.parametrize(
    "file_extension,expected_content_type",
    [
        pytest.param(
            ".zip",
            "application/zip",
            id="zip_file-should_use_application_zip_content_type",
        ),
        pytest.param(
            ".xml",
            "application/xml",
            id="xml_file-should_use_application_xml_content_type",
        ),
        pytest.param(
            ".csv", "text/csv", id="csv_file-should_use_text_csv_content_type"
        ),
        pytest.param(
            ".txt", "text/plain", id="txt_file-should_use_text_plain_content_type"
        ),
        pytest.param(
            ".unknown",
            "application/octet-stream",
            id="unknown_extension-should_use_octet_stream_content_type",
        ),
    ],
)
def test_put_object(s3_client, file_extension, expected_content_type):
    """Test putting objects with different content types"""
    s3, bucket_name, mock_client = s3_client
    mock_client.put_object.return_value = None

    result = s3.put_object(f"test_file{file_extension}", b"test string")

    assert result is True
    mock_client.put_object.assert_called_once_with(
        Bucket=bucket_name,
        Key=f"test_file{file_extension}",
        Body=b"test string",
        ContentType=expected_content_type,
    )


@pytest.mark.parametrize(
    "operation,method,error_message,test_input",
    [
        pytest.param(
            "put_object",
            "put_object",
            "Put object failed",
            b"test string",
            id="put_object-should_handle_failed_upload",
        ),
        pytest.param(
            "get_object",
            "get_object",
            "Get object failed",
            None,
            id="get_object-should_handle_nonexistent_file",
        ),
        pytest.param(
            "download_fileobj",
            "download_fileobj",
            "Get object failed",
            None,
            id="download_fileobj-should_handle_download_failure",
        ),
    ],
)
def test_s3_operations_exceptions(
    s3_client, test_file_path, operation, method, error_message, test_input
):
    """Test exception handling for S3 operations"""
    s3, _, mock_client = s3_client

    error_response = {"Error": {"Code": "NoSuchKey", "Message": error_message}}

    getattr(mock_client, method).side_effect = ClientError(error_response, operation)

    with pytest.raises(ClientError) as exc_info:
        if operation == "put_object":
            s3.put_object(test_file_path, test_input)
        else:
            getattr(s3, method)(test_file_path)

    assert error_message in str(exc_info.value)


@pytest.mark.parametrize(
    "mock_pages,prefix,expected_results",
    [
        pytest.param(
            [
                {"Contents": [{"Key": "file1.txt"}, {"Key": "file2.txt"}]},
                {"Contents": [{"Key": "file3.txt"}, {"Key": "file4.txt"}]},
            ],
            "test-prefix",
            [
                {"Contents": [{"Key": "file1.txt"}, {"Key": "file2.txt"}]},
                {"Contents": [{"Key": "file3.txt"}, {"Key": "file4.txt"}]},
            ],
            id="multiple_pages-should_return_all_objects",
        ),
        pytest.param(
            [{"Contents": [{"Key": "single.txt"}]}],
            "single",
            [{"Contents": [{"Key": "single.txt"}]}],
            id="single_page-should_return_one_object",
        ),
        pytest.param(
            [], "empty-prefix", [], id="empty_result-should_return_empty_list"
        ),
    ],
)
def test_get_list_objects_v2(s3_client, mock_pages, prefix, expected_results):
    """Test listing objects with pagination"""
    s3, bucket_name, mock_client = s3_client

    mock_paginator = MagicMock()
    mock_client.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = mock_pages

    results = list(s3.get_list_objects_v2(prefix=prefix))

    assert results == expected_results
    mock_client.get_paginator.assert_called_once_with("list_objects_v2")
    mock_paginator.paginate.assert_called_once_with(Bucket=bucket_name, Prefix=prefix)


def test_download_fileobj(s3_client, test_file_path):
    """Test downloading file object"""
    s3, bucket_name, mock_client = s3_client
    mock_client.download_fileobj.return_value = None

    result = s3.download_fileobj(test_file_path)

    assert isinstance(result, BytesIO)
    mock_client.download_fileobj.assert_called_once_with(
        Bucket=bucket_name,
        Key=test_file_path,
        Fileobj=pytest.approx(result, abs=BytesIO()),
    )


@pytest.mark.parametrize(
    "mock_content,expected_filename",
    [
        pytest.param(
            b"Simple text content",
            "testfile.txt",
            id="simple_text-should_preserve_filename",
        ),
        pytest.param(
            b"Binary content\x00\x01",
            "testfile.txt",
            id="binary_content-should_handle_binary_data",
        ),
    ],
)
def test_download_to_tempfile_variations(
    s3_client, test_file_path, mock_content, expected_filename
):
    """Test downloading different types of content to tempfile"""
    s3, bucket_name, mock_client = s3_client

    def download_file_effect(**kwargs):
        fileobj = kwargs.get("Fileobj")
        fileobj.write(mock_content)

    mock_client.download_fileobj.side_effect = download_file_effect

    temp_file_path = s3.download_to_tempfile(test_file_path)

    try:
        assert temp_file_path.exists()
        assert temp_file_path.name == expected_filename
        assert temp_file_path.read_bytes() == mock_content
    finally:
        if temp_file_path.parent.exists():
            import shutil

            shutil.rmtree(temp_file_path.parent)


@pytest.mark.parametrize(
    "error_scenario",
    [
        pytest.param(
            {
                "error_code": "NoSuchKey",
                "error_message": "The specified key does not exist.",
                "operation": "GetObject",
            },
            id="missing_file-should_cleanup_and_raise_error",
        ),
        pytest.param(
            {
                "error_code": "AccessDenied",
                "error_message": "Access Denied",
                "operation": "GetObject",
            },
            id="access_denied-should_cleanup_and_raise_error",
        ),
    ],
)
def test_download_to_tempfile_failure(
    s3_client, test_file_path, tmp_path, error_scenario
):
    """Test handling of download failure including temp file cleanup"""
    s3, bucket_name, mock_client = s3_client

    # Setup error response
    error_response = {
        "Error": {
            "Code": error_scenario["error_code"],
            "Message": error_scenario["error_message"],
        }
    }
    mock_client.download_fileobj.side_effect = ClientError(
        error_response, error_scenario["operation"]
    )

    # Mock tempfile.mkdtemp to use pytest's tmp_path
    temp_dir = tmp_path / "s3_download_test"
    temp_dir.mkdir()

    with patch("tempfile.mkdtemp", return_value=str(temp_dir)):
        # Verify the temp directory exists before the operation
        assert temp_dir.exists()

        # Attempt download and expect failure
        with pytest.raises(ClientError) as exc_info:
            s3.download_to_tempfile(test_file_path)

        # Verify error details
        assert error_scenario["error_message"] in str(exc_info.value)

        # Verify S3 client was called correctly
        mock_client.download_fileobj.assert_called_once()
        call_kwargs = mock_client.download_fileobj.call_args[1]
        assert call_kwargs["Bucket"] == bucket_name
        assert call_kwargs["Key"] == test_file_path

        # Verify temp directory was cleaned up
        assert (
            not temp_dir.exists()
        ), "Temporary directory should be cleaned up after error"


def test_get_object(s3_client, mock_file_content, test_file_path):
    """Test getting object from S3"""
    s3, bucket_name, mock_client = s3_client
    mock_client.get_object.return_value = {"Body": mock_file_content}

    content = s3.get_object(test_file_path)

    assert content == mock_file_content
    mock_client.get_object.assert_called_once_with(
        Bucket=bucket_name, Key=test_file_path
    )
