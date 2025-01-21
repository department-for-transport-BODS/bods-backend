"""
Naptan Parser for XMLs
"""

from pathlib import Path
from typing import Any, Iterator

from common_layer.dynamodb.client_loader import DynamoDBLoader
from common_layer.txc.parser.parser_txc import strip_namespace
from common_layer.txc.parser.stop_points import parse_txc_stop_point
from lxml import etree
from structlog.stdlib import get_logger

from .download import download_file
from .file_utils import create_data_dir
from .parsers import (
    NAPTAN_NS_PREFIX,
    parse_descriptor,
    parse_location,
    parse_stop_areas,
    parse_stop_classification,
    parse_top_level,
)

log = get_logger()


def get_element_text(
    element: etree._Element | None, xpath: str, namespace: dict[str, str]
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


def validate_stop_point(stop_point: etree._Element) -> bool:
    """
    Validate if the stop point is active and not marked for deletion
    """
    return (
        stop_point.get("Status") == "active"
        and stop_point.get("Modification") != "delete"
    )


def clean_stop_data(stop_data: dict[str, Any]) -> dict[str, Any]:
    """
    Clean the final stop data by converting empty strings to None
    DynamoDB reject empty strings
    """
    return {k: (v if v not in ["", None] else None) for k, v in stop_data.items()}


def get_base_stop_data(stop_point: etree._Element) -> dict[str, Any]:
    """
    Extract base stop point data
    """
    return {
        "Status": "active",
        "CreationDateTime": stop_point.get("CreationDateTime") or None,
        "ModificationDateTime": stop_point.get("ModificationDateTime") or None,
        "RevisionNumber": stop_point.get("RevisionNumber") or None,
    }


def parse_stop_point(stop_point: etree._Element) -> dict[str, Any] | None:
    """
    Parse a single StopPoint XML into a Dictionary
    """
    try:
        if not validate_stop_point(stop_point):
            return None

        stop_data = get_base_stop_data(stop_point)

        location_data = parse_location(stop_point)
        if location_data is None:
            return None
        stop_data.update(location_data)

        field_data, atco_found = parse_top_level(stop_point)
        if not atco_found:
            return None
        stop_data.update(field_data)

        for parser, key in [
            (parse_descriptor, None),
            (parse_stop_classification, None),
            (parse_stop_areas, "StopAreas"),
        ]:
            parsed_data = parser(stop_point)
            if parsed_data:
                if key:
                    stop_data[key] = parsed_data
                else:
                    stop_data.update(parsed_data)

        return clean_stop_data(stop_data)

    # We need to Skip StopPoints with errors and process all stops
    except Exception:  # pylint: disable=broad-exception-caught
        log.error("Failed to parse stop point", exc_info=True)
        return None


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
            stop_point_without_ns = strip_namespace(stop_point)
            if stop_data := parse_txc_stop_point(stop_point_without_ns):
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


def load_naptan_data_from_xml(
    url: str, data_dir: Path, dynamo_loader: Any
) -> tuple[int, int]:
    """
    Process NaPTAN XML data from URL and load into DynamoDB.
    Returns tuple of (processed_count, error_count).
    """
    xml_path = prepare_naptan_data(url, data_dir)
    return process_naptan_data(xml_path, dynamo_loader)
