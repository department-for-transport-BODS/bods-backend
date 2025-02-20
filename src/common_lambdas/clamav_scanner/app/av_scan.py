"""
AV Scan Functions
"""

import os
from pathlib import Path
from typing import BinaryIO

from clamd import BufferTooLongError, ClamdNetworkSocket
from clamd import ConnectionError as ClamdConnectionError
from common_layer.exceptions.file_exceptions import (
    AntiVirusError,
    ClamConnectionError,
    SuspiciousFile,
)
from pydantic import ValidationError
from structlog.stdlib import get_logger

from .models import ClamAVConfig, ScanResult

log = get_logger()


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
