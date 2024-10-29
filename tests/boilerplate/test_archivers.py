import io
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from boilerplate.archiver import GTFSRTArchiver
from boilerplate.enums import CAVLDataFormat
from tests.mock_db import MockedDB

ARCHIVE_MODULE = "src.boilerplate.archiver"


@patch(ARCHIVE_MODULE + ".LambdaEvent")
def test_filename(mock_lambda_event):

    url = "https://fakeurl.zz/datafeed"
    archiver = GTFSRTArchiver({}, url)
    archiver._access_time = datetime(2020, 1, 1, 1, 1, 1)
    archiver._content = b"fakedata"
    expected_filename = "gtfsrt_2020-01-01_010101.zip"
    assert expected_filename == archiver.filename


@patch(ARCHIVE_MODULE + ".LambdaEvent")
def test_data_format_value(mock_lambda_event):
    url = "https://fakeurl.zz/datafeed"
    archiver = GTFSRTArchiver({}, url)
    assert archiver.data_format_value == "gtfsrt"


@patch(ARCHIVE_MODULE + ".LambdaEvent")
def test_access_time_value_error(mock_lambda_event):
    url = "https://fakeurl.zz/datafeed"

    archiver = GTFSRTArchiver({}, url)
    with pytest.raises(ValueError) as exc:
        archiver.access_time
        assert str(exc.value) == "`content` has not been fetched yet."


@patch(ARCHIVE_MODULE + ".LambdaEvent")
@patch(ARCHIVE_MODULE + ".requests")
def test_access_time(mrequests, mock_lambda_event):
    mrequests.get.return_value = Mock(content=b"response")
    url = "https://fakeurl.zz/datafeed"
    archiver = GTFSRTArchiver({}, url)
    archiver.content
    assert archiver.access_time is not None


@patch(ARCHIVE_MODULE + ".LambdaEvent")
def test_content_filename(mock_lambda_event):
    url = "https://fakeurl.zz/datafeed"
    archiver = GTFSRTArchiver({}, url)
    assert archiver.content_filename == "gtfsrt.bin"


@patch(ARCHIVE_MODULE + ".LambdaEvent")
def test_get_file(mock_lambda_event):
    url = "https://fakeurl.zz/datafeed"
    archiver = GTFSRTArchiver({}, url)
    archiver._content = b"content"
    bytesio = archiver.get_file(archiver._content)

    expected = io.BytesIO()
    with ZipFile(expected, mode="w", compression=ZIP_DEFLATED) as zf:
        zf.writestr("gtfsrt.bin", archiver._content)

    expected.seek(0)
    bytesio.seek(0)
    assert expected.read() == bytesio.read()


@patch(ARCHIVE_MODULE + ".GTFSRTArchiver.upload_file_to_s3")
@patch(ARCHIVE_MODULE + ".LambdaEvent")
def test_archive(mock_lambda_event, upload_files_to_s3):
    db_object = MockedDB()
    mock_object = MagicMock()
    mock_object.event = {}
    mock_object.db = db_object
    mock_lambda_event.return_value = mock_object
    upload_files_to_s3.return_value = None

    url = "https://fakeurl.zz/datafeed"
    archiver = GTFSRTArchiver({}, url)

    content = b"newcontent"
    access_time = datetime(2020, 1, 1, 12, 1, 1)

    archiver._content = content
    archiver._access_time = access_time
    cavl_data_archive = db_object.classes.avl_cavldataarchive

    assert db_object.session.query(cavl_data_archive).count() == 0
    archiver.archive()
    assert db_object.session.query(cavl_data_archive).count() == 1
    archive = db_object.session.query(cavl_data_archive).first()
    assert archive.data_format == CAVLDataFormat.GTFSRT.value


@patch(ARCHIVE_MODULE + ".GTFSRTArchiver.upload_file_to_s3")
@patch(ARCHIVE_MODULE + ".LambdaEvent")
def test_archive_if_existing_file(mock_lambda_event, upload_files_to_s3):
    db_object = MockedDB()
    mock_object = MagicMock()
    mock_object.event = {}
    mock_object.db = db_object
    mock_lambda_event.return_value = mock_object
    upload_files_to_s3.return_value = None

    url = "https://fakeurl.zz/datafeed"

    cavl_data_archive = db_object.classes.avl_cavldataarchive

    test_cavldataarchive = cavl_data_archive(
        id=1,
        data_format=CAVLDataFormat.GTFSRT.value,
        data=f"gtfsrt_2023-11-10_152636.zip",
    )
    db_object.session.add(test_cavldataarchive)
    db_object.session.flush()

    archiver = GTFSRTArchiver({}, url)

    content = b"newcontent"
    access_time = datetime(2020, 1, 1, 12, 1, 1)

    archiver._content = content
    archiver._access_time = access_time

    assert db_object.session.query(cavl_data_archive).count() == 1
    archiver.archive()
    assert db_object.session.query(cavl_data_archive).count() == 1
    archive = db_object.session.query(cavl_data_archive).first()
    assert archive.data_format == CAVLDataFormat.GTFSRT.value
