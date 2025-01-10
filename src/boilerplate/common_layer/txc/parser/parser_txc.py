"""
Parse TXC XML into Pydantic Models
"""

from io import BytesIO
from pathlib import Path

from lxml import etree
from lxml.etree import QName, _Element, parse
from pydantic import BaseModel, Field
from structlog.stdlib import get_logger

from ..models.txc_data import TXCData
from ..parser.metadata import parse_metadata
from .hashing import get_file_hash
from .journey_pattern_sections import parse_journey_pattern_sections
from .operators import parse_operators
from .route_sections import parse_route_sections
from .routes import parse_routes
from .serviced_organisation import parse_serviced_organisations
from .services import parse_services
from .stop_points import parse_stop_points
from .vehicle_journeys import parse_vehicle_journeys

log = get_logger()


class TXCParserConfig(BaseModel):
    """
    Configuration for TXC Parser to control which sections are parsed.
    All sections default to True except track_data and file_hash.
    """

    metadata: bool = Field(
        default=True, description="Parse metadata section", title="Parse Metadata"
    )
    serviced_organisations: bool = Field(
        default=True,
        description="Parse serviced organisations section",
        title="Parse Serviced Organisations",
    )
    stop_points: bool = Field(
        default=True, description="Parse stop points section", title="Parse Stop Points"
    )
    route_sections: bool = Field(
        default=True, description="Parse route sections", title="Parse Route Sections"
    )
    routes: bool = Field(
        default=True, description="Parse routes section", title="Parse Routes"
    )
    journey_pattern_sections: bool = Field(
        default=True,
        description="Parse journey pattern sections",
        title="Parse Journey Pattern Sections",
    )
    operators: bool = Field(
        default=True, description="Parse operators section", title="Parse Operators"
    )
    services: bool = Field(
        default=True, description="Parse services section", title="Parse Services"
    )
    vehicle_journeys: bool = Field(
        default=True,
        description="Parse vehicle journeys section",
        title="Parse Vehicle Journeys",
    )
    track_data: bool = Field(
        default=False,
        description="Parse track data in route sections",
        title="Parse Track Data",
    )
    file_hash: bool = Field(
        default=False,
        description="Calculate and include file hash in metadata",
        title="Parse File Hash",
    )

    @classmethod
    def parse_all(cls) -> "TXCParserConfig":
        """Create a config with all sections enabled (including track_data and file_hash)."""
        return cls(track_data=True, file_hash=True)

    def should_parse(self, section_name: str) -> bool:
        """Check if a section should be parsed based on config."""
        return getattr(self, section_name.lower(), True)


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
    xml_data: _Element,
    config: TXCParserConfig | None = None,
) -> TXCData:
    """
    Take an Input of a TXC XML Element and return a pydantic model.
    Optionally specify which sections to parse via config.
    """
    config = config or TXCParserConfig()

    # Handle route sections first since it's needed for routes
    route_sections = (
        parse_route_sections(xml_data, parse_track_data=config.track_data)
        if config.route_sections
        else []
    )

    txc_data = TXCData(
        Metadata=parse_metadata(xml_data, file_hash=None) if config.metadata else None,
        ServicedOrganisations=(
            parse_serviced_organisations(xml_data)
            if config.serviced_organisations
            else []
        ),
        StopPoints=parse_stop_points(xml_data) if config.stop_points else [],
        RouteSections=route_sections,
        Routes=parse_routes(xml_data, route_sections) if config.routes else [],
        JourneyPatternSections=(
            parse_journey_pattern_sections(xml_data)
            if config.journey_pattern_sections
            else []
        ),
        Operators=parse_operators(xml_data) if config.operators else [],
        Services=parse_services(xml_data) if config.services else [],
        VehicleJourneys=(
            parse_vehicle_journeys(xml_data) if config.vehicle_journeys else []
        ),
    )

    return txc_data


def parse_txc_file(
    filename: Path,
    config: TXCParserConfig | None = None,
) -> TXCData:
    """
    Take an Input of a TXC File and return a pydantic model.
    Optionally specify which sections to parse via config.
    """
    config = config or TXCParserConfig()

    file_hash = get_file_hash(filename) if config.file_hash else None

    xml_data = load_xml_data(filename)
    txc_data = parse_txc_from_element(xml_data, config)

    if file_hash and txc_data.Metadata:
        txc_data.Metadata.FileHash = file_hash

    return txc_data
