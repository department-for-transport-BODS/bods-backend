"""
Naptan Parser for XMLs
"""

from pathlib import Path
from typing import Any, Iterator

from boto3.dynamodb.types import TypeSerializer
from common_layer.dynamodb.client_loader import DynamoDBLoader
from lxml import etree
from structlog.stdlib import get_logger

from .download import download_file
from .file_utils import create_data_dir

log = get_logger()
NAPTAN_NAMESPACE = {"naptan": "http://www.naptan.org.uk/"}
NAPTAN_NS_PREFIX = "{" + NAPTAN_NAMESPACE["naptan"] + "}"
LOCATION_TAGS = {
    f"{NAPTAN_NS_PREFIX}Longitude": "Longitude",
    f"{NAPTAN_NS_PREFIX}Latitude": "Latitude",
    f"{NAPTAN_NS_PREFIX}Easting": "Easting",
    f"{NAPTAN_NS_PREFIX}Northing": "Northing",
}
DESCRIPTOR_TAGS = {
    f"{NAPTAN_NS_PREFIX}CommonName": "CommonName",
    f"{NAPTAN_NS_PREFIX}ShortCommonName": "ShortCommonName",
    f"{NAPTAN_NS_PREFIX}Street": "Street",
    f"{NAPTAN_NS_PREFIX}Landmark": "Landmark",
    f"{NAPTAN_NS_PREFIX}Indicator": "Indicator",
}


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


def parse_location(stop_point: etree._Element) -> dict[str, str] | None:
    """Extract location data from stop point with minimal traversal."""

    # Direct traversal to Translation element
    for location in stop_point.iter(f"{NAPTAN_NS_PREFIX}Translation"):
        result = {"Longitude": "", "Latitude": "", "Easting": "", "Northing": ""}

        for child in location:
            if child.tag in LOCATION_TAGS:
                result[LOCATION_TAGS[child.tag]] = child.text or ""

        if result["Easting"] and result["Northing"]:
            return result

        return None

    return None


def parse_descriptor(stop_point: etree._Element) -> dict[str, str]:
    """Extract descriptor data from stop point with minimal traversal."""
    descriptor_tag = f"{NAPTAN_NS_PREFIX}Descriptor"

    # Direct traversal to find Descriptor element
    for descriptor in stop_point:
        if descriptor.tag == descriptor_tag:
            result = {
                "CommonName": "",
                "ShortCommonName": "",
                "Street": "",
                "Landmark": "",
                "Indicator": "",
            }

            for child in descriptor:
                if child.tag in DESCRIPTOR_TAGS:
                    result[DESCRIPTOR_TAGS[child.tag]] = child.text or ""

            return result

    return {
        "CommonName": "",
        "ShortCommonName": "",
        "Street": "",
        "Landmark": "",
        "Indicator": "",
    }


def parse_stop_areas(stop_point: etree._Element) -> list[str]:
    """Extract stop areas from stop point using direct traversal."""
    stop_areas_tag = f"{NAPTAN_NS_PREFIX}StopAreas"
    stop_area_ref_tag = f"{NAPTAN_NS_PREFIX}StopAreaRef"
    result = []

    # Direct traversal to find StopAreas
    for stop_areas in stop_point.iter(stop_areas_tag):
        for area_ref in stop_areas.iter(stop_area_ref_tag):
            if area_ref.get("Status") == "active" and area_ref.text:
                result.append(area_ref.text)

    return result


def parse_stop_point(stop_point: etree._Element) -> dict[str, Any] | None:
    """
    Parse a single StopPoint XML into a Dictionary
    The Stop is skipped if:
        - Status != active
        - Modification = delete
        - Easting or Northing missing
    """
    try:
        # Early validation
        if (
            stop_point.get("Status") != "active"
            or stop_point.get("Modification") == "delete"
        ):
            return None

        # Initialize with attributes
        stop_data: dict[str, str | list[str]] = {
            "Status": "active",
            "CreationDateTime": stop_point.get("CreationDateTime", ""),
            "ModificationDateTime": stop_point.get("ModificationDateTime", ""),
            "RevisionNumber": stop_point.get("RevisionNumber", ""),
        }

        # Get location data first as it's a common rejection point
        location_data = parse_location(stop_point)
        if location_data is None:
            return None

        # Add validated location data
        stop_data.update(location_data)

        # Single pass through direct children for required and optional fields
        atco_found = False
        for child in stop_point:
            tag = child.tag
            text = child.text

            if not text:
                continue

            if tag == f"{NAPTAN_NS_PREFIX}AtcoCode":
                stop_data["AtcoCode"] = text
                atco_found = True
            elif tag == f"{NAPTAN_NS_PREFIX}NaptanCode":
                stop_data["NaptanCode"] = text
            elif tag == f"{NAPTAN_NS_PREFIX}LocalityName":
                stop_data["LocalityName"] = text
            elif tag == f"{NAPTAN_NS_PREFIX}StopType":
                stop_data["StopType"] = text

        if not atco_found:
            return None

        # Add descriptor data
        descriptor_data = parse_descriptor(stop_point)
        stop_data.update(descriptor_data)

        # Add stop areas if present
        stop_areas = parse_stop_areas(stop_point)
        if stop_areas:
            stop_data["StopAreas"] = stop_areas

        return stop_data

    # Ensure that for any exception processing a StopPoint, we return None and continue
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
            if stop_data := parse_stop_point(stop_point):
                current_batch.append(stop_data)

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


def prepare_dynamo_items(
    stops: list[dict[str, Any]], serializer: TypeSerializer
) -> Iterator[dict[str, Any]]:
    """Convert stop data to DynamoDB format."""
    for stop in stops:
        try:
            yield {k: serializer.serialize(v) for k, v in stop.items() if v is not None}
        # Ensure that for any exception processing a StopPoint, we return None and continue
        except Exception:  # pylint: disable=broad-exception-caught
            log.error(
                "Failed to serialize stop for DynamoDB",
                stop_data=stop,
                exc_info=True,
            )


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
    """
    processed_count = 0
    error_count = 0
    batch: list[dict[str, Any]] = []

    # Process stops in batches
    for stop_batch in stream_stops(xml_path):
        for item in prepare_dynamo_items(stop_batch, dynamo_loader.serializer):
            batch.append(item)

            if len(batch) >= dynamo_loader.batch_size:
                unprocessed = dynamo_loader.batch_write_items(batch, "put")
                error_count += len(unprocessed)
                processed_count += len(batch) - len(unprocessed)
                batch = []

    # Process remaining items
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
