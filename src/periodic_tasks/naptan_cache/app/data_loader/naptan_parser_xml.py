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
    except Exception as e:
        log.error("Failed to download NaPTAN XML", error=str(e), exc_info=True)
        raise


def parse_element_children(
    element: etree._Element | None, fields: dict[str, str]
) -> dict[str, str]:
    """Extract specified fields from element's children."""
    if element is None:
        return {}

    for child in element:
        tag = etree.QName(child).localname
        if tag in fields and child.text:
            fields[tag] = child.text

    return fields


def parse_location(
    stop_point: etree._Element, namespace: dict[str, str]
) -> dict[str, str] | None:
    """Extract location data from stop point."""
    location_data = stop_point.find(".//naptan:Location/naptan:Translation", namespace)
    if location_data is None:
        return None

    result = {"Longitude": "", "Latitude": "", "Easting": "", "Northing": ""}

    for child in location_data:
        tag = etree.QName(child).localname
        if tag in result and child.text:
            result[tag] = child.text

    if result["Easting"] == "" or result["Northing"] == "":
        return None

    return result


def parse_descriptor(
    stop_point: etree._Element, namespace: dict[str, str]
) -> dict[str, str]:
    """Extract descriptor data from stop point."""
    descriptor = stop_point.find("naptan:Descriptor", namespace)
    return parse_element_children(
        descriptor,
        {
            "CommonName": "",
            "ShortCommonName": "",
            "Street": "",
            "Landmark": "",
            "Indicator": "",
        },
    )


def parse_stop_areas(
    stop_point: etree._Element, namespace: dict[str, str]
) -> list[str]:
    """Extract stop areas from stop point."""
    stop_areas_elem = stop_point.find(".//naptan:StopAreas", namespace)
    if stop_areas_elem is None:
        return []

    return [
        area.text
        for area in stop_areas_elem.findall(".//naptan:StopAreaRef", namespace)
        if area.get("Status") == "active" and area.text
    ]


def parse_stop_point(
    stop_point: etree._Element, namespace: dict[str, str]
) -> dict[str, Any] | None:
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

        location_data = parse_location(stop_point, namespace)
        if location_data is None:
            return None

        atco_code = stop_point.find("naptan:AtcoCode", namespace)
        if atco_code is None or not atco_code.text:
            return None

        # Build stop data incrementally
        stop_data: dict[str, str | list[str]] = {
            "ATCOCode": atco_code.text,
            "Status": "active",
            "CreationDateTime": stop_point.get("CreationDateTime", ""),
            "ModificationDateTime": stop_point.get("ModificationDateTime", ""),
            "RevisionNumber": stop_point.get("RevisionNumber", ""),
        }

        # Add already validated location data
        stop_data.update(location_data)

        # Add descriptor data
        stop_data.update(parse_descriptor(stop_point, namespace))

        # Handle optional fields with single find() and check
        optional_fields = {
            "NaptanCode": "naptan:NaptanCode",
            "LocalityName": ".//naptan:LocalityName",
            "StopType": ".//naptan:StopType",
        }

        for field, xpath in optional_fields.items():
            if value := get_element_text(stop_point, xpath, namespace):
                stop_data[field] = value

        # Add stop areas if present
        stop_areas = parse_stop_areas(stop_point, namespace)
        if stop_areas:
            stop_data["StopAreas"] = stop_areas

        return stop_data

    except Exception as e:
        log.error("Failed to parse stop point", error=str(e), exc_info=True)
        return None


def stream_stops(
    xml_path: Path, batch_size: int = 25
) -> Iterator[list[dict[str, Any]]]:
    """Stream stop points from XML in batches."""
    namespace = {"naptan": "http://www.naptan.org.uk/"}
    log.info("Starting to stream stops from XML", file_path=str(xml_path))

    context = etree.iterparse(
        str(xml_path),
        events=("end",),
        tag=f'{{{namespace["naptan"]}}}StopPoint',
        remove_blank_text=True,
        remove_comments=True,
    )

    current_batch: list[dict[str, Any]] = []

    try:
        for _, stop_point in context:
            if stop_data := parse_stop_point(stop_point, namespace):
                current_batch.append(stop_data)

                if len(current_batch) >= batch_size:
                    yield current_batch
                    current_batch = []

            # Clean up processed element
            stop_point.clear()
            parent = stop_point.getparent()
            previous = stop_point.getprevious()
            if parent is not None and previous is not None:
                parent.remove(previous)

        if current_batch:
            yield current_batch

    except Exception as e:
        log.error("Failed to parse XML file", error=str(e), exc_info=True)
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
        except Exception as e:
            log.error(
                "Failed to serialize stop for DynamoDB",
                error=str(e),
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
