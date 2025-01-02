"""
Description: Module to scan incoming s3 file object for vulnerabilities.
Lambda handle is triggered by S3 event
"""

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from clamd import BufferTooLongError, ClamdNetworkSocket
from clamd import ConnectionError as ClamdConnectionError
from common_layer.database.client import SqlDB
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo,
)
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.exceptions.file_exceptions import (
    AntiVirusError,
    ClamConnectionError,
    SuspiciousFile,
)
from common_layer.json_logging import configure_logging
from common_layer.s3 import S3
from common_layer.txc.parser.hashing import get_file_hash
from common_layer.zip import process_zip_to_s3
from pydantic import BaseModel, Field, ValidationError
from structlog.stdlib import get_logger

log = get_logger()


class ClamAVScannerInputData(BaseModel):
    """
    Lambda Input Data
    """

    class Config:
        """
        Allow us to map Bucket / Object Key
        """

        populate_by_name = True

    s3_bucket_name: str = Field(alias="Bucket")
    s3_file_key: str = Field(alias="ObjectKey")
    revision_id: int = Field(alias="DatasetRevisionId")


class ClamAVConfig(BaseModel):
    """
    Config Vars for ClamAV
    """

    host: str
    port: int


@dataclass
class ScanResult:
    """
    Virus Scan Result with Optional Reason
    """

    status: str
    reason: str | None = None


class FileScanner:
    """Class used to scan files for viruses.

    Args:
        config: ClamAVConfig containing host and port for ClamAV scanner

    Examples:
        >>> scanner = FileScanner(ClamAVConfig(host="clamavhost.example", port=9876))
        >>> scanner.scan(Path("/tmp/file_to_scan.zip"))

    Raises:
        ClamConnectionError: if can't connect to Clamd
        AntiVirusError: if an error occurs during scanning
        SuspiciousFile: if a suspicious file is found
    """

    def __init__(self, config: ClamAVConfig):
        """Initialize scanner with ClamAV network connection"""
        log.info("Antivirus scan: Started")
        self.config = config
        self.clamav = ClamdNetworkSocket(host=config.host, port=config.port)

    def scan(self, file_path: Path) -> None:
        """
        Scan a file at the given path for viruses

        Args:
            file_path: Path to the file to scan
        """
        try:
            with file_path.open("rb") as file_:
                result = self._perform_scan(file_)

            if result.status == "ERROR":
                log.error("Antivirus scan: FAILED", result=result)
                raise AntiVirusError(filename=str(file_path))
            if result.status == "FOUND":
                log.warning("Antivirus scan: FOUND", reason=result.reason)
                if result.reason:
                    raise SuspiciousFile(
                        filename=str(file_path), message=f"Virus found: {result.reason}"
                    )
                raise SuspiciousFile(filename=str(file_path))

            log.info("Antivirus scan: OK", file_path=str(file_path))

        except (OSError, IOError) as e:
            msg = f"Failed to read file for virus scan: {e}"
            log.exception(msg)
            raise AntiVirusError(filename=str(file_path), message=msg) from e

    def _perform_scan(self, file_: BinaryIO) -> ScanResult:
        """
        Perform the ClamAV scan on an open file

        Returns:
            ScanResult with status and optional reason
        """
        try:
            response = self.clamav.instream(file_)
            if not response:
                log.info(
                    "ClamAV Did not respond",
                    host=self.config.host,
                    port=self.config.port,
                )
                raise AntiVirusError(
                    filename=str(file_.name), message="No response received from ClamAV"
                )

            # ClamAV response is dict with stream tuple of (status, signature)
            scan_tuple = response.get("stream")
            if (
                not scan_tuple
                or not isinstance(scan_tuple, tuple)
                or len(scan_tuple) != 2
            ):
                raise AntiVirusError(
                    filename=str(file_.name),
                    message=f"Invalid response format from ClamAV: {response}",
                )

            status, reason = scan_tuple
            return ScanResult(
                status=str(status), reason=str(reason) if reason else None
            )

        except BufferTooLongError as e:
            msg = "Antivirus scan failed due to BufferTooLongError"
            log.exception(msg)
            raise AntiVirusError(filename=str(file_.name), message=msg) from e

        except ClamdConnectionError as e:
            msg = "Antivirus scan failed due to ConnectionError"
            log.exception(msg)
            raise ClamConnectionError(filename=str(file_.name), message=msg) from e


def calculate_and_update_file_hash(
    db: SqlDB,
    input_data: ClamAVScannerInputData,
    file_path: Path,
):
    """
    Fetch the File from S3

    Update the database dataset revision with the File Hash
    """
    file_hash = get_file_hash(file_path)
    log.debug("Generated File Hash", hash=file_hash)

    OrganisationDatasetRevisionRepo(db).update_original_file_hash(
        input_data.revision_id, file_hash
    )
    log.info(
        "Generated File Hash and updated original_file_hash column in Dataset Revision",
        revision_id=input_data.revision_id,
        file_hash=file_hash,
        file_path=str(file_path),
    )


def get_clamav_config() -> ClamAVConfig:
    """
    Get Config for ClamAV
    """
    log.info("Loading ClamAV configuration from environment")

    try:
        host = os.environ["CLAMAV_HOST"]
        port_str = os.environ["CLAMAV_PORT"]

        try:
            port = int(port_str)
        except ValueError as exc:
            log.error("Invalid ClamAV port number", port=port_str)
            raise EnvironmentError(
                f"CLAMAV_PORT must be a number, got: {port_str}"
            ) from exc

        config = ClamAVConfig(host=host, port=port)

        log.info(
            "ClamAV configuration loaded successfully",
            host=config.host,
            port=config.port,
        )

        return config

    except KeyError as e:
        missing_var = e.args[0]
        log.error("Missing required environment variable", variable=missing_var)
        raise EnvironmentError(
            f"Required environment variable {missing_var} is not set"
        ) from e
    except ValidationError as e:
        log.error("Invalid ClamAV configuration", errors=e.errors())
        raise


def av_scan_file(clam_av_config: ClamAVConfig, file_to_scan: Path) -> None:
    """
    Scan the file with a scanner
    """
    # Connect/Scan the file object
    av_scanner = FileScanner(clam_av_config)

    # Check if ClamAV is responding
    if not av_scanner.clamav.ping():
        raise ClamConnectionError("ClamAV is not running or accessible.")
    av_scanner.scan(file_to_scan)


def process_file_to_s3(s3_client: S3, file_path: Path, destination_prefix: str) -> str:
    """
    Copy a single file and upload it to S3 in a dedicated folder.
    State Machine Map does not work on single files, requires a folder
    """
    file_name = file_path.name
    folder_name = f"{destination_prefix.rstrip('/')}_{Path(file_name).stem}/"
    s3_key = f"{folder_name}{file_name}"

    log.info(
        "Copying single file into a new folder",
        file_path=str(file_path),
        destination=folder_name,
    )

    try:
        with open(file_path, "rb") as file:
            s3_client.put_object(s3_key, file.read())
            log.debug(
                "Successfully uploaded file to new location",
                filename=file_name,
                s3_key=s3_key,
            )

        log.info(
            "Completed file processing",
            file_path=str(file_path),
            destination=folder_name,
        )

        return folder_name

    except Exception as e:
        log.error(
            "Failed to copy file to new location",
            file_path=str(file_path),
            s3_key=s3_key,
            error=str(e),
        )
        raise


def unzip_and_upload_files(s3_handler: S3, file_path: Path) -> str:
    """
    If the file is a zip, unzip and upload its contents to S3.
    Otherwise, copy the single file to a new folder and return that folder path.
    """
    if file_path.suffix.lower() == ".zip":
        log.info("Input File is a Zip. Processing...", file_path=str(file_path))
        return process_zip_to_s3(
            s3_client=s3_handler, zip_path=file_path, destination_prefix="ext"
        )

    log.info("Input file is a single file", path=str(file_path))
    return process_file_to_s3(
        s3_client=s3_handler, file_path=file_path, destination_prefix="ext"
    )


@file_processing_result_to_db(step_name=StepName.CLAM_AV_SCANNER)
def lambda_handler(event, _context):
    """
    Main lambda handler
    """
    configure_logging()
    input_data = ClamAVScannerInputData(**event)
    s3_handler = S3(bucket_name=input_data.s3_bucket_name)
    clam_av_config = get_clamav_config()
    db = SqlDB()

    try:
        # Fetch the object from s3
        downloaded_file_path = s3_handler.download_to_tempfile(
            file_path=input_data.s3_file_key
        )

        try:
            # Calculate hash and scan file
            calculate_and_update_file_hash(db, input_data, downloaded_file_path)
            av_scan_file(clam_av_config, downloaded_file_path)

            # Handle zip extraction if needed
            generated_prefix = unzip_and_upload_files(
                s3_handler=s3_handler, file_path=Path(downloaded_file_path)
            )

            msg = (
                f"Successfully scanned the file '{input_data.s3_file_key}' "
                f"from bucket '{input_data.s3_bucket_name}'"
            )

            log.info(
                "Sucessfully processed input file", generated_prefix=generated_prefix
            )

            return {
                "statusCode": 200,
                "body": {
                    "message": msg,
                    "generatedPrefix": generated_prefix,
                },
            }

        finally:
            # Clean up the temp file
            shutil.rmtree(Path(downloaded_file_path).parent)

    except Exception as e:
        log.error(
            "Error processing file",
            file_key=input_data.s3_file_key,
            bucket=input_data.s3_bucket_name,
            error=str(e),
        )
        raise
