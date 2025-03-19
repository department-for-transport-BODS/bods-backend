"""
Naptan Parser for XMLs
"""

import asyncio
from pathlib import Path
from typing import Any, AsyncIterator

from botocore.exceptions import ClientError
from common_layer.dynamodb.client_loader import DynamoDBLoader
from common_layer.xml.txc.parser.parser_txc import strip_namespace
from common_layer.xml.txc.parser.stop_points import parse_txc_stop_point
from lxml import etree
from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from .download import download_file
from .file_utils import create_data_dir
from .xml_constants import NAPTAN_NS_PREFIX

log = get_logger()


def get_element_text(
    element: _Element | None, xpath: str, namespace: dict[str, str]
) -> str:
    """Efficiently extract text from an XML element using direct access when possible."""
    if element is None:
        return ""

    result = element.find(xpath, namespace)
    return result.text if result is not None and result.text else ""


def download_naptan_xml(url: str, data_dir: Path) -> Path:
    """Download the NaPTAN XML file."""
    try:
        local_path = download_file(
            url=url,
            allowed_extensions=[".xml"],
            dest_folder=data_dir,
            max_size_mb=600,
        )
        log.info("Successfully downloaded NaPTAN XML", file_path=str(local_path))
        return local_path
    except Exception:
        log.error("Failed to download NaPTAN XML", exc_info=True)
        raise


def prepare_naptan_data(url: str, data_dir: Path) -> Path:
    """
    Download and prepare NaPTAN data for processing.
    Returns path to the downloaded XML file.
    """
    log.info("Preparing an Output Path", path=str(data_dir))
    new_data_dir = create_data_dir(data_dir)
    log.info("Output dir set", path=str(new_data_dir))
    log.info("Downloading Naptan Data", url=url)
    return download_naptan_xml(url, data_dir)


async def async_stream_stop_points(xml_path: Path) -> AsyncIterator[dict[str, Any]]:
    """
    Stream stop points from XML file.
    Uses iterparse for memory efficiency and validates stop points before processing.
    """
    context = etree.iterparse(
        str(xml_path),
        events=("end",),
        tag=f"{NAPTAN_NS_PREFIX}StopPoint",
        remove_blank_text=True,
        remove_comments=True,
        collect_ids=False,
        resolve_entities=False,
        remove_pis=True,
        strip_cdata=True,
        huge_tree=True,
        compact=True,
        no_network=True,
    )

    try:
        for _, stop_point in context:
            stop_point = strip_namespace(stop_point)

            if stop_data := parse_txc_stop_point(stop_point):
                yield stop_data.model_dump()

            # Clean up processed elements
            stop_point.clear()
            parent = stop_point.getparent()
            previous = stop_point.getprevious()
            if parent is not None and previous is not None:
                parent.remove(previous)

    except Exception:
        await log.aerror("Failed to parse XML file", exc_info=True)
        raise
    finally:
        del context


async def process_stop_points(
    stop_points_stream: AsyncIterator[dict[str, Any]], dynamo_loader: DynamoDBLoader
) -> tuple[int, int]:
    """
    Process stream of stop points using concurrent DynamoDB transactions.
    Returns (processed_count, error_count).
    """
    total_processed = 0
    total_errors = 0
    active_tasks: list[asyncio.Task[tuple[int, int]]] = []
    current_batch: list[dict[str, Any]] = []

    transaction_size = 100

    async def process_batch(items: list[dict[str, Any]]) -> tuple[int, int]:
        return await dynamo_loader.async_transact_write_items(items)

    async def wait_for_slot() -> None:
        """Wait for a task slot to become available and process completed tasks."""
        nonlocal total_processed, total_errors, active_tasks

        done, pending = await asyncio.wait(
            active_tasks, return_when=asyncio.FIRST_COMPLETED
        )

        for completed_task in done:
            try:
                processed, errors = await completed_task
                total_processed += processed
                total_errors += errors
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                error_message = e.response.get("Error", {}).get("Message", "No message")
                await log.aerror(
                    "AWS operation failed",
                    error_code=error_code,
                    error_message=error_message,
                )
                total_errors += transaction_size
            except ValueError as e:
                await log.aerror("Failed to process batch result", error=str(e))
                total_errors += transaction_size

        active_tasks = list(pending)

    try:
        async for stop_point in stop_points_stream:
            current_batch.append(stop_point)

            if len(current_batch) >= transaction_size:
                # Wait for a slot if we're at max concurrency
                while len(active_tasks) >= dynamo_loader.max_concurrent_batches:
                    await wait_for_slot()

                # Create new task
                task = asyncio.create_task(process_batch(current_batch))
                active_tasks.append(task)
                current_batch = []

        # Process any remaining items
        if current_batch:
            task = asyncio.create_task(process_batch(current_batch))
            active_tasks.append(task)

        # Wait for all remaining tasks to complete
        while active_tasks:
            await wait_for_slot()

    except Exception:
        await log.aerror("Failed to process stop points", exc_info=True)
        raise

    await log.ainfo(
        "Completed stop point processing",
        processed_count=total_processed,
        error_count=total_errors,
    )

    return total_processed, total_errors


def load_naptan_data_from_xml(
    url: str, data_dir: Path, dynamo_loader: DynamoDBLoader
) -> tuple[int, int]:
    """
    Process NaPTAN XML data from URL and load into DynamoDB.
    Returns tuple of (processed_count, error_count).
    """
    xml_path = prepare_naptan_data(url, data_dir)
    stream = async_stream_stop_points(xml_path)
    return asyncio.run(process_stop_points(stream, dynamo_loader))
