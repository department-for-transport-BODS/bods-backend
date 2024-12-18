"""
File Hashing Functionality
"""

import hashlib
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
