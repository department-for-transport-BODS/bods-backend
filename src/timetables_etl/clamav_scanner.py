"""
Description: Module to scan incoming s3 file object for vulnerabilities.
Lambda handle is triggered by S3 event
"""

import os
from dataclasses import dataclass
from typing import BinaryIO, Optional

from clamd import BufferTooLongError, ClamdNetworkSocket, ConnectionError
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.db.repositories.dataset_revision import update_file_hash_in_db
from common_layer.exceptions.file_exceptions import (
    AntiVirusError,
    ClamConnectionError,
    SuspiciousFile,
)
from common_layer.logger import logger
from common_layer.s3 import S3
from common_layer.utils import sha1sum
from common_layer.zip import unzip

SCAN_ATTEMPTS = 5
MULTIPLIER = 1


@dataclass
class ScanResult:
    status: str
    reason: Optional[str] = None


class FileScanner:
    """Class used to scan for viruses.

    Args:
        host(str): Host path of ClamAV scannner.
        port(srt): Post of ClamAV scanner.

    Examples:
        >>> scanner = FileScanner("http://clamavhost.example", 9876)
        >>> f = open("suspect/file.zip", "rb")
        >>> scanner.scan(f)
        >>> f.close()

    Raises:
        ClamConnectionError: if cant connect to Clamd.
        AntiVirusError: if an error occurs during scanning.
        SuspiciousFile: if a suspicious file is found.

    """

    def __init__(self, host: str, port: int):
        """Scan f with ClamAV antivirus scanner"""
        logger.info("Antivirus scan: Started")
        self.clamav = ClamdNetworkSocket(host=host, port=port)

    def scan(self, file_: BinaryIO):
        try:
            result = self._perform_scan(file_)
        except Exception as exc:
            raise exc

        if result.status == "ERROR":
            logger.info("Antivirus scan: FAILED")
            raise AntiVirusError(file_.name)
        elif result.status == "FOUND":
            logger.exception("Antivirus scan: FOUND")
            raise SuspiciousFile(file_.name, result.reason)
        logger.info("Antivirus scan: OK")

    def _perform_scan(self, file_: BinaryIO) -> ScanResult:
        try:
            response = self.clamav.instream(file_)
            status, reason = response["stream"]
            return ScanResult(status=status, reason=reason)
        except BufferTooLongError as e:
            msg = "Antivirus scan failed due to BufferTooLongError"
            logger.exception(msg, exc_info=True)
            raise AntiVirusError(file_.name, message=msg) from e
        except ConnectionError as e:
            msg = "Antivirus scan failed due to ConnectionError"
            logger.exception(msg, exc_info=True)
            raise ClamConnectionError(file_.name, message=msg) from e


@file_processing_result_to_db(step_name=StepName.CLAM_AV_SCANNER)
def lambda_handler(event, context):
    """
    Main lambda handler
    """
    # Extract the bucket name and object key from the S3 event
    bucket = event["Bucket"]
    key = event["ObjectKey"]

    # URL-decode the key if it has special characters
    key = key.replace("+", " ")

    try:
        # Get S3 handler
        s3_handler = S3(bucket_name=bucket)

        # Fetch the object from s3
        file_object = s3_handler.get_object(file_path=key)

        update_file_hash_in_db(
            event["ObjectKey"],
            event["DatasetRevisionId"],
            original_file_hash=sha1sum(file_object.read()),
        )

        # Connect/Scan the file object
        av_scanner = FileScanner(
            os.environ["CLAMAV_HOST"], int(os.environ["CLAMAV_PORT"])
        )

        # Check if ClamAV is responding
        if not av_scanner.clamav.ping():
            raise ClamConnectionError("ClamAV is not running or accessible.")

        # Backward compatibility with python file handler
        file_object = s3_handler.get_object(file_path=key)
        file_object.name = key
        av_scanner.scan(file_object)  # noqa
        msg = f"Successfully scanned the file '{key}' from bucket '{bucket}'"

        prefix = unzip(s3_client=s3_handler, file_path=key, prefix="ext") \
            if key.endswith("zip") else ''

        return {
            "statusCode": 200,
            "body": {
                "message": msg,
                "generatedPrefix": prefix,
            },
        }
    except Exception as e:
        logger.error(f"Error scanning object '{key}' from bucket '{bucket}'")
        raise e
