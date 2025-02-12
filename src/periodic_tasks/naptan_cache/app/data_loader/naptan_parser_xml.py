"""
Naptan Parser for XMLs
"""

import asyncio
from pathlib import Path
from typing import Any, Iterator

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


def validate_stop_point(stop_point: _Element) -> bool:
    """
    Validate if the stop point is active and not marked for deletion
    """
    return (
        stop_point.get("Status") == "active"
        and stop_point.get("Modification") != "delete"
    )


def stream_stops(
    xml_path: Path, batch_size: int = 25
) -> Iterator[list[dict[str, Any]]]:
    """Stream stop points from XML in batches."""
    log.info("Starting to stream stops from XML", file_path=str(xml_path))

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

    current_batch: list[dict[str, Any]] = []

    try:
        for _, stop_point in context:
            stop_point = strip_namespace(stop_point)
            if stop_data := parse_txc_stop_point(stop_point):
                stop_point_dict = stop_data.model_dump()
                current_batch.append(stop_point_dict)

                if len(current_batch) >= batch_size:
                    yield current_batch
                    current_batch = []

            # Remove Processed Elements from Memory
            stop_point.clear()
            parent = stop_point.getparent()
            previous = stop_point.getprevious()
            if parent is not None and previous is not None:
                parent.remove(previous)

        if current_batch:
            yield current_batch

    except Exception:
        log.error("Failed to parse XML file", exc_info=True)
        raise
    finally:
        del context


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


def process_naptan_data(
    xml_path: Path, dynamo_loader: DynamoDBLoader
) -> tuple[int, int]:
    """
    Process NaPTAN XML file and load into DynamoDB.
    Returns tuple of (processed_count, error_count).
    DynamoDB's batch_write_tiems only supports 25 at a time
    If more speed is required, then multithreading is required
    """
    processed_count = 0
    error_count = 0
    batch: list[dict[str, Any]] = []

    for stop_batch in stream_stops(xml_path):
        for item in stop_batch:
            batch.append(item)

            if len(batch) >= dynamo_loader.batch_size:
                unprocessed = dynamo_loader.batch_write_items(batch, "put")
                error_count += len(unprocessed)
                processed_count += len(batch) - len(unprocessed)
                batch = []

    if batch:
        unprocessed = dynamo_loader.batch_write_items(batch, "put")
        error_count += len(unprocessed)
        processed_count += len(batch) - len(unprocessed)

    log.info(
        "Completed NaPTAN data processing",
        processed_count=processed_count,
        error_count=error_count,
    )

    return processed_count, error_count


async def async_process_naptan_data(
    xml_path: Path, dynamo_loader: DynamoDBLoader, concurrent_batches: int = 10
) -> tuple[int, int]:
    """
    Process NaPTAN XML file and load into DynamoDB using concurrent batches.
    DynamoDB batch_write_item has a limit of 25 items per request.
    We'll collect multiple batches of 25 items before triggering concurrent processing.
    """
    total_processed = 0
    total_errors = 0
    current_batch: list[dict[str, Any]] = []

    batch_target: int = dynamo_loader.batch_size * concurrent_batches

    for stop_batch in stream_stops(xml_path):
        current_batch.extend(stop_batch)

        if len(current_batch) >= batch_target:
            processed, errors = await dynamo_loader.async_batch_write_items(
                current_batch
            )
            total_processed += processed
            total_errors += errors
            current_batch = []

    if current_batch:
        processed, errors = await dynamo_loader.async_batch_write_items(current_batch)
        total_processed += processed
        total_errors += errors

    log.info(
        "Completed NaPTAN data processing",
        processed_count=total_processed,
        error_count=total_errors,
    )

    return total_processed, total_errors


def load_naptan_data_from_xml(
    url: str, data_dir: Path, dynamo_loader: Any
) -> tuple[int, int]:
    """
    Process NaPTAN XML data from URL and load into DynamoDB.
    Returns tuple of (processed_count, error_count).
    """
    xml_path = prepare_naptan_data(url, data_dir)
    return asyncio.run(async_process_naptan_data(xml_path, dynamo_loader))
