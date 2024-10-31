"""
Description: Module to scan incoming s3 file object for vulnerabilities.
Lambda handle is triggered by S3 event
"""

import io
import json
import logging
import os
from typing import BinaryIO, Optional
from dataclasses import dataclass
from clamd import BufferTooLongError, ClamdNetworkSocket
from clamd import ConnectionError as ClamdConnectionError
from tenacity import (
    before_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)
from logger import logger
from s3 import S3

SCAN_ATTEMPTS = 5
MULTIPLIER = 1


# TODO: removed this class import the exception from boilerplate/exceptions
class ValidationException(Exception):
    code = "VALIDATION_FAILED"
    message_template = "Validation failed for {filename}."

    def __init__(self, filename, line=1, message=None):
        self.filename = filename
        if message is None:
            self.message = self.message_template.format(filename=filename)
        else:
            self.message = message
        self.line = line


class AntiVirusError(ValidationException):
    """Base exception for antivirus scans."""

    code = "ANTIVIRUS_FAILURE"
    message_template = "Antivirus failed validating file {filename}."


class SuspiciousFile(AntiVirusError):
    """Exception for when a suspicious file is found."""

    code = "SUSPICIOUS_FILE"
    message_template = "Anti-virus alert triggered for file {filename}."


class ClamConnectionError(AntiVirusError):
    """Exception for when we can't connect to the ClamAV server."""

    code = "AV_CONNECTION_ERROR"
    message_template = "Could not connect to Clam daemon when \
                        testing {filename}."


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
        except ClamdConnectionError as exc:
            raise ClamConnectionError(file_.name) from exc

        if result.status == "ERROR":
            logger.info("Antivirus scan: FAILED")
            raise AntiVirusError(file_.name)
        elif result.status == "FOUND":
            logger.exception("Antivirus scan: FOUND")
            raise SuspiciousFile(file_.name, result.reason)
        logger.info("Antivirus scan: OK")

    @retry(
        reraise=True,
        retry=retry_if_exception_type(ClamdConnectionError),
        wait=wait_random_exponential(multiplier=MULTIPLIER, max=10),
        stop=stop_after_attempt(SCAN_ATTEMPTS),
        before=before_log(logger, logging.DEBUG),
    )
    def _perform_scan(self, file_: BinaryIO) -> ScanResult:
        try:
            response = self.clamav.instream(file_)
            status, reason = response["stream"]
            return ScanResult(status=status, reason=reason)
        except BufferTooLongError as e:
            msg = "Antivirus scan failed due to BufferTooLongError"
            logger.exception(msg, exc_info=True)
            raise AntiVirusError(file_.name, message=msg) from e


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
            raise Exception("ClamAV is not running or accessible.")

        # Backward compatibility with python file handler
        file_object.name = key
        av_scanner.scan(file_object)  # noqa
    except ValidationException as err:
        logger.error(err.message, exc_info=True)
        raise err
    except Exception as e:
        logger.error(f"Error scanning object '{key}' from bucket '{bucket}'")
        raise e

    # Return a success message
    return {
        "statusCode": 200,
        "body": f"Successfully scanned the file '{key}' from bucket '{bucket}'",
    }
