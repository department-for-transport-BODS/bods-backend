"""
Parse TXC XML into Pydantic Models
"""

import hashlib
from io import BytesIO
from pathlib import Path

from lxml import etree
from lxml.etree import QName, _Element, parse
from structlog.stdlib import get_logger

from ..models.txc_data import TXCData
from ..parser.metadata import parse_metadata
from .journey_pattern_sections import parse_journey_pattern_sections
from .operators import parse_operators
from .route_sections import parse_route_sections
from .routes import parse_routes
from .services import parse_services
from .stop_points import parse_stop_points
from .vehicle_journeys import parse_vehicle_journeys

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


def strip_namespace(xml_data: _Element) -> _Element:
    """
    Strip namespace prefixes from element tags.
    """
    for elem in xml_data.iter():
        tag = elem.tag.text if isinstance(elem.tag, QName) else elem.tag
        if isinstance(tag, str) and "}" in tag:
            elem.tag = tag.split("}", 1)[1]
    return xml_data


def load_xml_data(filename: Path | BytesIO) -> _Element:
    """
    Load the XML Data and strip namespaces for ease of query
    """
    log.info("Opening TXC file", filename=filename)
    parser = etree.XMLParser()
    tree = parse(filename, parser)
    return strip_namespace(tree.getroot())


def parse_txc_from_element(
    xml_data: _Element, parse_track_data: bool = False, file_hash: str | None = None
) -> TXCData:
    """
    Take an Input of a TXC XML Element and return a pydantic model
    """
    route_sections = parse_route_sections(xml_data, parse_track_data)
    txc_data = TXCData(
        Metadata=parse_metadata(xml_data, file_hash),
        StopPoints=parse_stop_points(xml_data),
        RouteSections=route_sections,
        Routes=parse_routes(xml_data, route_sections),
        JourneyPatternSections=parse_journey_pattern_sections(xml_data),
        Operators=parse_operators(xml_data),
        Services=parse_services(xml_data),
        VehicleJourneys=parse_vehicle_journeys(xml_data),
    )

    return txc_data


def parse_txc_file(
    filename: Path, parse_track_data: bool = False, parse_file_hash: bool = False
) -> TXCData:
    """
    Take an Input of a TXC File and return a pydantic model
    """
    file_hash = None
    if parse_file_hash:
        file_hash = get_file_hash(filename)
    xml_data = load_xml_data(filename)
    txc_data = parse_txc_from_element(xml_data, parse_track_data, file_hash)

    return txc_data
