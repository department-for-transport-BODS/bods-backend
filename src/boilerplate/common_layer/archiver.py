"""
Module to support different dataset archiving to S3
"""

from datetime import datetime, timezone
from io import BytesIO
import time
from os import environ
from zipfile import ZIP_DEFLATED, ZipFile

import requests
from requests import RequestException
from structlog.stdlib import get_logger
from common_layer.database.client import SqlDB
from common_layer.database.models import AvlCavlDataArchive
from common_layer.database.repos import AvlCavlDataArchiveRepo
from common_layer.enums import CAVLDataFormat
from common_layer.s3 import S3

log = get_logger()


class ArchivingError(Exception):
    """
    Exception for Archiving
    """


def upsert_cavl_table(db: SqlDB, data_format: str, file_name: str) -> None:
    """Update the record in the db if exist otherwise create a new record"""
    archive = AvlCavlDataArchiveRepo(db).get_by_data_format(data_format)
    if not archive:
        archive = AvlCavlDataArchive(
            data_format=data_format,
            data=file_name,
        )
        AvlCavlDataArchiveRepo(db).insert(archive)
    else:
        archive.data = file_name
        archive.last_updated = datetime.now(timezone.utc)
        AvlCavlDataArchiveRepo(db).update(archive)


class ConsumerAPIArchiver:
    """
    ConsumerAPIArchiver class
    """

    data_format = CAVLDataFormat.SIRIVM.value
    extension = ".xml"
    filename_prefix = "sirivm"
    content_filename_prefix = "siri"
    archiving_type = ""

    def __init__(self, url: str) -> None:
        self.url: str = url
        self.db: SqlDB = SqlDB()
        self._access_time: datetime | None = None
        self._content: bytes | None = None

    @property
    def filename(self) -> str:
        """Get the zip filename"""
        now = (self.access_time or datetime.now()).strftime("%Y-%m-%d_%H%M%S")
        return self.data_format_value + "_" + now + ".zip"

    @property
    def data_format_value(self) -> str:
        """Get the file format value"""
        return self.filename_prefix

    @property
    def access_time(self) -> datetime | None:
        """Get access time for request send to fetch url data"""
        if self._content is None:
            raise ValueError("`content` has not been fetched yet.")

        if self._access_time is None:
            raise ValueError("`access_time` has not been set.")

        return self._access_time

    @property
    def content(self) -> bytes:
        """Get the file content"""
        if self._content is None:
            self._content = self._get_content()
        return self._content

    @property
    def content_filename(self) -> str:
        """Get content filename"""
        return self.content_filename_prefix + self.extension

    def archive(self) -> None:
        """Archive the file"""
        file_ = self.get_file(self.content)
        self.save_to_database(file_)

    def _get_content(self) -> bytes:
        """Helper function to get the content of file from url"""
        try:
            response = requests.get(self.url, timeout=60)
            self._access_time = datetime.now(timezone.utc)
            log.info(
                "Total time elapsed to get response",
                url=self.url,
                archiving_type=self.archiving_type,
                time=response.elapsed.total_seconds(),
            )
            return response.content
        except RequestException as err:
            msg = f"Unable to retrieve data from {self.url}"
            log.error(
                "Unable to retrive data",
                url=self.url,
                archiving_type=self.archiving_type,
            )
            raise ArchivingError(msg) from err

    def get_file(self, content: bytes) -> BytesIO:
        """Get the zip file content"""
        start_get_file_op = time.time()
        bytesio = BytesIO()
        with ZipFile(bytesio, mode="w", compression=ZIP_DEFLATED) as zf:
            zf.writestr(self.content_filename, content)
        end_file_op = time.time()
        log.info(
            "Zipping file operation completed",
            archiving_type=self.archiving_type,
            time=end_file_op - start_get_file_op,
        )

        return bytesio

    def save_to_database(self, bytesio: BytesIO) -> None:
        """Save the archived details to database"""
        start_s3_op = time.time()
        self.upload_file_to_s3(bytesio.getvalue())
        upsert_cavl_table(self.db, self.data_format, self.filename)

        end_s3_op = time.time()
        log.info(
            "S3 archiving and saving to DB operation completed",
            archiving_type=self.archiving_type,
            time=end_s3_op - start_s3_op,
            filename=self.filename,
        )

    def upload_file_to_s3(self, bytesio: bytes) -> None:
        """Upload the archived file to s3"""
        bucket_name = environ.get("AWS_SIRIVM_STORAGE_BUCKET_NAME", default="")
        s3 = S3(bucket_name)
        s3.put_object(self.filename, bytesio)


class SiriVMArchiver(ConsumerAPIArchiver):
    """Class supports sirivm file archiving"""

    data_format = CAVLDataFormat.SIRIVM.value
    extension = ".xml"
    filename_prefix = "sirivm"
    content_filename_prefix = "siri"
    archiving_type = "[SIRIVM_Archiving]"


class SiriVMTFLArchiver(ConsumerAPIArchiver):
    """Class supports sirivm tfl file archiving"""

    data_format = CAVLDataFormat.SIRIVM_TFL.value
    extension = ".xml"
    filename_prefix = "sirivm_tfl"
    content_filename_prefix = "siri_tfl"
    archiving_type = "[SIRIVM_TFL_Archiving]"


class GTFSRTArchiver(ConsumerAPIArchiver):
    """Class supports gtfsrt file archiving"""

    data_format = CAVLDataFormat.GTFSRT.value
    extension = ".bin"
    filename_prefix = "gtfsrt"
    content_filename_prefix = "gtfsrt"
    archiving_type = "[GTFSRT_Archiving]"
