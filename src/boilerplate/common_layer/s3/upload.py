"""
Zip Handling Utilities
"""

import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from typing import Coroutine, Generator, Iterator
from zipfile import BadZipFile, ZipFile

from botocore.exceptions import BotoCoreError, ClientError
from pydantic import BaseModel, Field
from structlog.stdlib import get_logger

from .client import S3

log = get_logger()


class ProcessingStats(BaseModel):
    """
    Zip Extract and Upload to S3 Stats
    """

    success_count: int = 0
    fail_count: int = 0
    skip_count: int = 0


class SharedContext(BaseModel):
    """Shared context data across all file operations"""

    temp_dir: str
    destination_prefix: str
    tags: dict[str, str] | None = None
    min_free_bytes: int
    processed_files: set[str] = Field(default_factory=set)


class FileContext(BaseModel):
    """File-specific context data"""

    file_path: str
    file_size: int
    shared: SharedContext


class NotEnoughDiskSpaceError(Exception):
    """Exception raised when there isn't enough disk space for extraction"""


def get_available_space(path: str) -> int:
    """Get available space in bytes for a given path"""
    usage = shutil.disk_usage(path)
    return usage.free


def get_space_info(temp_dir: str, min_free_bytes: int) -> dict[str, int]:
    """Get information about disk space for logging"""
    usage = shutil.disk_usage(temp_dir)
    return {
        "total_mb": usage.total // (1024 * 1024),
        "used_mb": usage.used // (1024 * 1024),
        "free_mb": usage.free // (1024 * 1024),
        "available_mb": (usage.free - min_free_bytes) // (1024 * 1024),
    }


def create_file_list(zip_obj: ZipFile) -> tuple[list[tuple[str, int]], int]:
    """
    Create sorted list of files in a Zip to process using a single pass
    Returns a tuple of (sorted_xml_files, skipped_count)
    Where sorted_xml_files is a list of tuples (file_path, file_size) sorted by size
    """
    xml_files_with_size: list[tuple[str, int]] = []
    skipped_count = 0

    for filename in zip_obj.namelist():
        if filename.endswith("/"):  # Skip directories
            continue

        # Normalize filename
        normalized = (
            filename.decode("cp437").encode("utf8").decode("utf8")
            if isinstance(filename, bytes)
            else filename
        )

        if normalized.lower().endswith(".xml"):
            file_size = zip_obj.getinfo(filename).file_size
            xml_files_with_size.append((normalized, file_size))
        else:
            skipped_count += 1

    sorted_xml_files = sorted(xml_files_with_size, key=lambda x: x[1])

    return sorted_xml_files, skipped_count


async def extract_and_upload_single_file(
    context: FileContext, zip_obj: ZipFile, s3_client: "S3"
) -> bool:
    """Extract and upload a single file, with space management
    Returns True on success, False on failure
    """
    # Skip if already processed
    if context.file_path in context.shared.processed_files:
        return True  # Consider this a success since it's already done

    # Wait for space to become available
    while (
        get_available_space(context.shared.temp_dir) - context.shared.min_free_bytes
        < context.file_size
    ):
        await asyncio.sleep(0.1)

    extracted_path = Path(context.shared.temp_dir) / context.file_path
    extracted_path.parent.mkdir(parents=True, exist_ok=True)
    s3_key = f"{context.shared.destination_prefix}{context.file_path}"

    try:
        # Extract the file
        with zip_obj.open(context.file_path) as source, open(
            extracted_path, "wb"
        ) as target:
            shutil.copyfileobj(source, target, length=8192)

        # Upload to S3
        with open(extracted_path, "rb") as file:
            await s3_client.put_object_async(
                s3_key, file.read(), tags=context.shared.tags
            )

        context.shared.processed_files.add(context.file_path)

        await log.adebug(
            "Successfully uploaded file",
            file_path=context.file_path,
            s3_key=s3_key,
            size_mb=context.file_size / (1024 * 1024),
        )

        return True

    except (OSError, IOError, ClientError, BotoCoreError) as err:
        await log.aerror(
            "Failed to extract or upload file",
            file_path=context.file_path,
            s3_key=s3_key,
            error=str(err),
            exc_info=True,
        )
        return False

    finally:
        # Remove file to save disk space
        if extracted_path.exists():
            try:
                os.unlink(extracted_path)
            except OSError:
                await log.aerror(
                    "Failed to cleanup extracted file",
                    path=str(extracted_path),
                    exc_info=True,
                )


async def process_file_with_semaphore(
    context: FileContext,
    zip_obj: ZipFile,
    s3_client: "S3",
    semaphore: asyncio.Semaphore,
) -> bool:
    """Process a single file with semaphore-controlled concurrency
    Returns True on success, False on failure
    """
    async with semaphore:
        return await extract_and_upload_single_file(context, zip_obj, s3_client)


async def process_batch(
    batch: list[tuple[str, int]],
    zip_obj: ZipFile,
    s3_client: "S3",
    shared_context: SharedContext,
    semaphore: asyncio.Semaphore,
) -> list[bool]:
    """Process a single batch of files concurrently"""
    # Process this batch concurrently
    tasks: list[Coroutine[None, None, bool]] = []
    for file_path, file_size in batch:
        file_context = FileContext(
            file_path=file_path,
            file_size=file_size,
            shared=shared_context,
        )
        tasks.append(
            process_file_with_semaphore(file_context, zip_obj, s3_client, semaphore)
        )

    # Gather results and update stats
    return await asyncio.gather(*tasks)


def batch_items(
    items: list[tuple[str, int]], batch_size: int
) -> Iterator[tuple[int, list[tuple[str, int]]]]:
    """
    Generate batches from a list of XML files with their sizes

    Args:
        items: List of (file_path, file_size) tuples
        batch_size: Size of each batch

    Yields:
        Tuples of (batch_number, batch_items)
    """
    total_items = len(items)
    for i in range(0, total_items, batch_size):
        yield i // batch_size, items[i : min(i + batch_size, total_items)]


async def process_zip_contents(
    zip_obj: ZipFile, s3_client: "S3", zip_path: Path, shared_context: SharedContext
) -> tuple[str, "ProcessingStats"]:
    """Process contents of a zip file using a shared context"""
    xml_files, skipped_count = create_file_list(zip_obj)
    stats = ProcessingStats()
    stats.skip_count = skipped_count

    if not xml_files:
        await log.ainfo("No XML files found in zip", zip_path=str(zip_path))
        return shared_context.destination_prefix, stats

    total_files = len(xml_files)

    await log.ainfo(
        "Starting batch processing",
        total_files=total_files,
        space_info=get_space_info(
            shared_context.temp_dir, shared_context.min_free_bytes
        ),
    )

    semaphore = asyncio.Semaphore(20)
    batch_size = 50
    for batch_num, batch in batch_items(xml_files, batch_size):

        results = await process_batch(
            batch,
            zip_obj,
            s3_client,
            shared_context,
            semaphore,
        )

        await log.ainfo(
            "Batch completed",
            batch=batch_num + 1,
            total_batches=(len(xml_files) + batch_size - 1) // batch_size,
            processed=len(shared_context.processed_files),
            total_files=total_files,
            space_info=get_space_info(
                shared_context.temp_dir, shared_context.min_free_bytes
            ),
            remaining_files=total_files - len(shared_context.processed_files),
        )
        stats.success_count += sum(1 for result in results if result)
        stats.fail_count += sum(1 for result in results if not result)

    await log.ainfo(
        "Completed batch zip processing",
        zip_path=str(zip_path),
        destination=shared_context.destination_prefix,
        files_processed=stats.success_count,
        files_failed=stats.fail_count,
        files_skipped=stats.skip_count,
    )

    return shared_context.destination_prefix, stats


async def process_zip_to_s3_async(
    s3_client: "S3",
    zip_path: Path,
    destination_prefix: str,
    tags: dict[str, str] | None = None,
    max_concurrent: int = 50,
) -> tuple[str, "ProcessingStats"]:
    """
    Process all files in a zip to S3, managing space efficiently in batches
    """

    min_free_bytes = 10 * 1024 * 1024  # 10MB safety buffer

    await log.ainfo(
        "Processing zip file in batches",
        zip_path=str(zip_path),
        destination=destination_prefix,
        max_concurrent=max_concurrent,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Create a shared context for the whole process
            shared_context = SharedContext(
                temp_dir=temp_dir,
                destination_prefix=destination_prefix,
                tags=tags,
                min_free_bytes=min_free_bytes,
            )

            with ZipFile(zip_path) as zip_obj:
                return await process_zip_contents(
                    zip_obj=zip_obj,
                    s3_client=s3_client,
                    zip_path=zip_path,
                    shared_context=shared_context,
                )

        except (OSError, BadZipFile):
            await log.aerror(
                "Critical error processing zip file",
                zip_path=str(zip_path),
                exc_info=True,
            )
            raise


def extract_zip_file(zip_path: Path) -> Generator[tuple[str, Path], None, None]:
    """
    Extract files from zip one at a time to a temporary location
    With cleanup after each to reduce disk space consumption

    Yields:
        Tuple of (original filename, path to extracted file)
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            with ZipFile(zip_path) as zip_obj:
                file_list: list[str] = [
                    (
                        f.decode("cp437").encode("utf8").decode("utf8")
                        if isinstance(f, bytes)
                        else f
                    )
                    for f in zip_obj.namelist()
                    if not f.endswith("/")
                ]

                for file_path in file_list:
                    extracted_path = Path(temp_dir) / file_path
                    extracted_path.parent.mkdir(parents=True, exist_ok=True)

                    try:
                        with zip_obj.open(file_path) as source, open(
                            extracted_path, "wb"
                        ) as target:
                            shutil.copyfileobj(source, target, length=8192)

                        yield file_path, extracted_path

                    except (OSError, IOError):
                        log.error(
                            "Failed to extract file from zip",
                            file_path=file_path,
                            exc_info=True,
                        )
                        raise
                    finally:
                        try:
                            if extracted_path.exists():
                                os.unlink(extracted_path)
                                log.debug(
                                    "Cleaned up extracted file",
                                    path=str(extracted_path),
                                )
                        except OSError:
                            log.error(
                                "Failed to cleanup extracted file",
                                path=str(extracted_path),
                                exc_info=True,
                            )

        except BadZipFile:
            log.error("Invalid zip file", zip_path=zip_path, exc_info=True)
            raise


def is_xml_file(file_path: str) -> bool:
    """
    Check if a file is an XML file based on its extension.
    """
    return Path(file_path).suffix.lower() == ".xml"


def process_zip_to_s3(
    s3_client: "S3", zip_path: Path, destination_prefix: str
) -> tuple[str, ProcessingStats]:
    """Process a zip file and upload its contents to S3."""
    stats = ProcessingStats()

    log.info(
        "Processing zip file", zip_path=str(zip_path), destination=destination_prefix
    )

    try:
        for filename, extracted_path in extract_zip_file(zip_path):
            if not filename.lower().endswith(".xml"):
                log.debug("Skipping non-XML file", filename=filename)
                stats.skip_count += 1
                continue

            s3_key = f"{destination_prefix}{filename}"

            try:
                with open(extracted_path, "rb") as file:
                    s3_client.put_object(s3_key, file.read())

                log.debug(
                    "Successfully uploaded XML file", filename=filename, s3_key=s3_key
                )
                stats.success_count += 1

            except (IOError, ClientError):
                log.error(
                    "Failed to upload file to S3",
                    filename=filename,
                    s3_key=s3_key,
                    exc_info=True,
                )
                stats.fail_count += 1

        log.info(
            "Completed zip processing",
            zip_path=str(zip_path),
            destination=destination_prefix,
            files_processed=stats.success_count,
            files_failed=stats.fail_count,
            files_skipped=stats.skip_count,
        )

        return destination_prefix, stats

    except (OSError, BadZipFile):
        log.error(
            "Critical error processing zip file",
            zip_path=str(zip_path),
            exc_info=True,
        )
        raise


def process_file_to_s3(
    s3_client: S3, file_path: Path, destination_prefix: str
) -> tuple[str, ProcessingStats]:
    """
    Copy a single file and upload it to S3 in a dedicated folder.
    State Machine Map does not work on single files, requires a folder
    """
    stats = ProcessingStats()
    file_name = file_path.name
    s3_key = f"{destination_prefix}{file_name}"

    log.info(
        "Copying single file into a new folder",
        file_path=str(file_path),
        destination=destination_prefix,
    )

    try:
        with open(file_path, "rb") as file:
            s3_client.put_object(s3_key, file.read())
            log.debug(
                "Successfully uploaded file to new location",
                filename=file_name,
                s3_key=s3_key,
            )

        stats.success_count += 1

        log.info(
            "Completed file processing",
            file_path=str(file_path),
            destination=destination_prefix,
            files_processed=stats.success_count,
            files_failed=stats.fail_count,
            files_skipped=stats.skip_count,
        )

        return destination_prefix, stats

    except Exception:
        log.error(
            "Failed to copy file to new location",
            file_path=str(file_path),
            s3_key=s3_key,
            exc_info=True,
        )
        stats.fail_count += 1
        raise
