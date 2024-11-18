
"""
Description: Module to scan incoming s3 file object for vulnerabilities.
Lambda handle is triggered by S3 event
"""
import json
import os
from typing import BinaryIO, Optional
from dataclasses import dataclass
from clamd import BufferTooLongError, ClamdNetworkSocket, ConnectionError
from logger import logger
from s3 import S3
from boilerplate.db.file_processing_result import file_processing_result_to_db
from boilerplate.exceptions.file_exceptions import (
    AntiVirusError,
    ClamConnectionError,
    SuspiciousFile
)

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


@file_processing_result_to_db(step_name="Clam AV Scanner")
def lambda_handler(event, context):
    """
    Main lambda handler
    """
    logger.info(f"Received event:{json.dumps(event, indent=2)}")

    # Extract the bucket name and object key from the S3 event
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]

    # URL-decode the key if it has special characters
    key = key.replace("+", " ")

    try:
        # Get S3 handler
        s3_handler = S3(bucket_name=bucket)

        # Fetch the object from S3
        file_object = s3_handler.get_object(file_path=key)

        # Connect/Scan the file object
        av_scanner = FileScanner(
            os.environ["CLAMAV_HOST"], int(os.environ["CLAMAV_PORT"])
        )

        # Check if ClamAV is responding
        if not av_scanner.clamav.ping():
            raise ClamConnectionError("ClamAV is not running or accessible.")

        # Backward compatibility with python file handler
        file_object.name = key
        av_scanner.scan(file_object)  # noqa
    except Exception as e:
        logger.error(f"Error scanning object '{key}' from bucket '{bucket}'")
        raise e

    # Return a success message
    return {
        "statusCode": 200,
        "body": f"Successfully scanned the file '{key}' from bucket '{bucket}'",
    }
