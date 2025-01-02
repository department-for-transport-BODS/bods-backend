"""
File Hashing Functionality
"""

import hashlib
from io import BytesIO
from pathlib import Path

from structlog.stdlib import get_logger

log = get_logger()


def get_file_hash(file_path: Path) -> str:
    """
    Get the hash of the txc file
    """
    log.info("Parsing TXC File hash", file_path=file_path)
    sha1 = hashlib.sha1()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha1.update(chunk)
    file_hash = sha1.hexdigest()
    log.info("TXC File Hash Calculated", file_hash=file_hash)
    return file_hash


def get_bytes_hash(bytes_io: BytesIO) -> str:
    """
    Get the SHA1 hash of a BytesIO object
    To make sure that we're not changing things, we should save and restore the position
    """
    log.info("Calculating hash of BytesIO object")
    sha1 = hashlib.sha1()

    # Save current position
    original_position = bytes_io.tell()

    # Reset to beginning of stream
    bytes_io.seek(0)

    # Read in chunks and update hash
    for chunk in iter(lambda: bytes_io.read(8192), b""):
        sha1.update(chunk)

    # Restore original position
    bytes_io.seek(original_position)

    file_hash = sha1.hexdigest()
    log.info("Hash calculated", file_hash=file_hash)
    return file_hash
