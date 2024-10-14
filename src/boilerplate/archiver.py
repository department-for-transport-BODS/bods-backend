import io
import requests
import time
import pytz
from datetime import datetime, timezone
from enums import CAVLDataFormat
from logger import logger
from os import environ
from requests import RequestException
from s3 import S3
from zipfile import ZIP_DEFLATED, ZipFile

from db.avl_cavldataarchive import (
    get_cavl_db_object,
    update_record_in_db,
)
from common import LambdaEvent


class ArchivingError(Exception):
    pass


class ConsumerAPIArchiver:
    data_format = CAVLDataFormat.SIRIVM.value
    extension = ".xml"
    filename_prefix = "sirivm"

    def __init__(self, event, url):
        self.url = url
        self.event = LambdaEvent(event)
        self._archive = self.get_object()
        self._access_time = None
        self._content = None

    @property
    def filename(self):
        now = self.access_time.strftime("%Y-%m-%d_%H%M%S")
        return self.data_format_value + "_" + now + ".zip"

    @property
    def data_format_value(self):
        return self.filename_prefix

    @property
    def access_time(self):
        if self._content is None:
            raise ValueError("`content` has not been fetched yet.")

        if self._access_time is None:
            raise ValueError("`access_time` has not been set.")

        return self._access_time

    @property
    def content(self):
        if self._content is None:
            self._content = self._get_content()
        return self._content

    @property
    def content_filename(self):
        return self.data_format_value + self.extension

    def archive(self):
        file_ = self.get_file(self.content)
        self.save_to_database(file_)

    def _get_content(self):
        try:
            response = requests.get(self.url)
        except RequestException:
            msg = f"Unable to retrieve data from {self.url}"
            logger.error(msg)
            raise ArchivingError(msg)
        else:
            self._access_time = datetime.now(timezone.utc)
            logger.info(
                f"{self.logger_prefix} Total time elapsed to get response from {self.url} is {response.elapsed.total_seconds()} for job-task_create_{self.filename_prefix}_zipfile"
            )
            return response.content

    def get_file(self, content):
        start_get_file_op = time.time()
        bytesio = io.BytesIO()
        with ZipFile(bytesio, mode="w", compression=ZIP_DEFLATED) as zf:
            zf.writestr(self.content_filename, content)
        end_file_op = time.time()
        logger.info(
            f"{self.logger_prefix} File operation took {end_file_op-start_get_file_op:.2f} seconds for job-task_create_{self.filename_prefix}_zipfile"
        )
        return bytesio

    def get_object(self):
        start_db_op = time.time()
        archive = get_cavl_db_object(self.event, self.data_format)
        end_db_op = time.time()
        logger.info(
            f"{self.logger_prefix} File operation took {end_db_op-start_db_op:.2f} seconds for job-task_create_{self.filename_prefix}_zipfile"
        )
        return archive

    def save_to_database(self, bytesio):
        start_s3_op = time.time()
        self.upload_file_to_s3(bytesio)
        self._archive.data = self.filename
        self._archive.last_updated = datetime.now(timezone.utc)
        update_record_in_db(self._archive, self.event)
        end_s3_op = time.time()
        logger.info(
            f"{self.logger_prefix} S3 archive operation took {end_s3_op-start_s3_op:.2f} seconds for job-task_create_{self.filename_prefix}_zipfile"
        )

    def upload_file_to_s3(self, bytesio):
        BUCKET_NAME = environ.get("AWS_SIRIVM_STORAGE_BUCKET_NAME", default="")
        s3 = S3(self.filename, bytesio, BUCKET_NAME)
        s3.upload_file()
        return


class SiriVMArchiver(ConsumerAPIArchiver):
    data_format = CAVLDataFormat.SIRIVM.value
    extension = ".xml"
    filename_prefix = "sirivm"
    logger_prefix = "[SIRIVM_Archiving]"


class SiriVMTFLArchiver(ConsumerAPIArchiver):
    data_format = CAVLDataFormat.SIRIVM_TFL.value
    extension = ".xml"
    filename_prefix = "sirivm_tfl"
    logger_prefix = "[SIRIVM_TFL_Archiving]"


class GTFSRTArchiver(ConsumerAPIArchiver):
    data_format = CAVLDataFormat.GTFSRT.value
    extension = ".bin"
    filename_prefix = "gtfsrt"
    logger_prefix = "[GTFSRT_Archiving]"
