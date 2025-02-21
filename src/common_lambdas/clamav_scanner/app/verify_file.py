"""
Functions to Verify the Zip meets ingest Requirements
"""

import zipfile
from pathlib import Path

from structlog.stdlib import get_logger

from .exceptions import NestedZipForbidden, ZipTooLarge

log = get_logger()


def check_for_nested_zips(zip_path: Path) -> tuple[bool, list[str]]:
    """
    Check if a ZIP file contains any nested ZIP files.
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            contents = zip_ref.namelist()
            nested_zips = [name for name in contents if name.lower().endswith(".zip")]
            has_nested = bool(nested_zips)

            if has_nested:
                log.info(
                    "Nested Zips Found",
                    zip_path=zip_path,
                    count=len(nested_zips),
                    nested_files=nested_zips,
                )

            return has_nested, nested_zips

    except zipfile.BadZipFile:
        log.error("File is Not a Zip File", zip_path=zip_path)
        return False, []
    except FileNotFoundError:
        log.error("File not Found", zip_path=zip_path)
        return False, []


def check_zip_uncompressed_size(
    zip_path: Path, max_size_bytes: int = 200_000_000  # Default 200mb
) -> tuple[bool, int]:
    """
    Check if the total uncompressed size of files in a ZIP would exceed a maximum size.
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            contents = zip_ref.filelist
            total_size = sum(info.file_size for info in contents)
            is_within_limit = total_size <= max_size_bytes

            log.info(
                "Zip Size Check Complete",
                zip_path=zip_path,
                total_size=total_size,
                max_size=max_size_bytes,
                within_limit=is_within_limit,
                file_count=len(contents),
            )

            return is_within_limit, total_size

    except zipfile.BadZipFile:
        log.error("File is Not a Zip File", zip_path=zip_path)
        return False, 0
    except FileNotFoundError:
        log.error("File not Found", zip_path=zip_path)
        return False, 0


def verify_zip_file(path: Path) -> None:
    """
    Verify that the Zip file meets requirements
    """
    nested_zip_result, _ = check_for_nested_zips(path)
    if nested_zip_result:
        raise NestedZipForbidden

    uncompressed_size_result, total_size = check_zip_uncompressed_size(path)
    if not uncompressed_size_result:
        raise ZipTooLarge
    log.info(
        "Zip File Verification Passed", path=path, total_uncompressed_size=total_size
    )
