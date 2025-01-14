"""
File checking and creation utils
"""

import os
import tempfile
from pathlib import Path

from structlog.stdlib import get_logger

log = get_logger()


def create_writable_directory(directory: Path) -> bool:
    """
    Create a directory if it doesn't exist and check if it's writable
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        return directory.is_dir() and os.access(directory, os.W_OK)
    except OSError as e:
        log.error(
            "Failed to create or access directory.",
            dir=str(directory),
            error=str(e),
            exc_info=True,
        )
        return False


def is_directory_writable(directory: Path) -> bool:
    """
    Check if directory is writable
    """
    if not os.access(directory, os.W_OK):
        log.warning("Directory is not writable.", dir=str(directory))
        return False
    return True


def get_temp_dir(original_path: Path) -> Path:
    """
    Prepend a temp dir to the original path
    """
    return Path(tempfile.gettempdir()) / original_path.name


def create_data_dir(path: Path) -> Path:
    """
    Try to use data dir or use tmp
    """
    try:
        if not create_writable_directory(path):
            raise PermissionError(f"Directory is not writable: {path}")
    except (FileNotFoundError, PermissionError) as exception:
        temp_data_dir = get_temp_dir(path)
        if not create_writable_directory(temp_data_dir):
            raise PermissionError(
                f"Temporary directory is also not writable: {temp_data_dir}"
            ) from exception

        log.info(
            "Using temporary directory.",
            dir=str(temp_data_dir),
        )
        path = temp_data_dir

    return path
