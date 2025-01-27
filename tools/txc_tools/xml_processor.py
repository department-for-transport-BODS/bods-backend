"""
Module defines helper functions to process xml TxC data
"""

import zipfile
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any, Callable

import structlog
from common_layer.txc.models.txc_data import TXCData
from common_layer.txc.models.txc_stoppoint import TXCStopPoint
from common_layer.txc.parser.parser_txc import load_xml_data, parse_txc_from_element

from .models import AnalysisMode, WorkerConfig, XMLFileInfo, XMLTagInfo, XmlTxcInventory
from .utils import count_tags_in_xml, get_size_mb

log = structlog.stdlib.get_logger()


def get_txc_object(**kwargs: dict[str, Any]) -> XmlTxcInventory:
    """
    Parse the XML, returns XMLTxCInventory object
    """
    parent_zip = kwargs.pop("parent_zip")
    filename = kwargs.get("filename")
    xml_file = kwargs.get("xml_file")

    if isinstance(filename, str):
        filename = Path(filename)

    # Validate xml_file
    if not isinstance(xml_file, BytesIO):
        raise ValueError("xml_file must be a file-like object (BytesIO) or a Path")

    # Validate filename
    if not isinstance(filename, (Path, BytesIO)):
        raise ValueError("filename must be of type Path or BytesIO")

    log.debug(
        "Parsing XML File with TxC parser", filename=filename, parent_zip=parent_zip
    )

    txc_object = parse_txc_from_element(load_xml_data(xml_file))
    return generate_txc_row_data(txc_object, filename)


def get_tag_size_object(**kwargs: dict[str, Any]) -> XMLFileInfo | XMLTagInfo:
    """
    Parse the xml, returns XMLTagInfo/XMLSizeInfo object
    """
    parent_zip = kwargs.get("parent_zip")
    filename = kwargs.get("filename")
    xml_file = kwargs.get("xml_file")
    tag_name = str(kwargs.get("tag_name", ""))
    assert isinstance(xml_file, BytesIO)

    parent_zip = str(parent_zip) if parent_zip else None

    log.debug(
        "Parsing and searching XML File", filename=filename, parent_zip=parent_zip
    )
    if kwargs.get("mode") == AnalysisMode.TAG:
        count = count_tags_in_xml(xml_file.read(), tag_name)
        return XMLTagInfo(
            file_path=str(filename), tag_count=count, parent_zip=parent_zip
        )

    size_mb = get_size_mb(xml_file)
    return XMLFileInfo(file_path=str(filename), size_mb=size_mb, parent_zip=parent_zip)


XML_OBJECTS: dict[
    AnalysisMode, Callable[..., XMLFileInfo | XMLTagInfo | XmlTxcInventory]
] = {
    AnalysisMode.SIZE: get_tag_size_object,
    AnalysisMode.TAG: get_tag_size_object,
    AnalysisMode.TXC: get_txc_object,
}


def process_xml_file(**kwargs) -> XMLFileInfo | XMLTagInfo | XmlTxcInventory:
    """
    Process a single XML file and return its information (size or tag count).
    """
    mode = kwargs.get("mode")

    if not isinstance(mode, AnalysisMode):
        raise ValueError("mode must be an instance of ReportMode")

    xml_file = kwargs.get("xml_file")
    if not hasattr(xml_file, "read"):
        raise ValueError("xml_file must be a file-like object with a 'read' method")
    return XML_OBJECTS[mode](**kwargs)


def generate_txc_row_data(txc: TXCData, file_path: Path | BytesIO) -> XmlTxcInventory:
    """
    Generate Row Data
    """
    log.info("Generating TxC row data for report inventory", file_path=file_path)
    operator = txc.Operators[0]
    service = txc.Services[0]
    line = service.Lines[0]

    if service.StartDate and service.EndDate:
        duration = (service.EndDate - service.StartDate).days
    else:
        duration = ""

    custom_stop_points = sum(
        1 for stop in txc.StopPoints if isinstance(stop, TXCStopPoint)
    )

    service_start_date = (
        service.StartDate if isinstance(service.StartDate, date) else None
    )
    service_end_date = service.EndDate if isinstance(service.EndDate, date) else None

    return XmlTxcInventory(
        national_operator_code=operator.NationalOperatorCode,
        operator_short_name=operator.OperatorShortName,
        line_name=line.LineName,
        service_code=service.ServiceCode,
        out_bound_description=(
            line.OutboundDescription.Description if line.OutboundDescription else ""
        ),
        in_bound_description=(
            line.InboundDescription.Description if line.InboundDescription else ""
        ),
        total_stop_points=len(txc.StopPoints),
        custom_stop_points=custom_stop_points,
        route_sections=len(txc.RouteSections),
        routes=len(txc.Routes),
        journey_pattern_sections=len(txc.JourneyPatternSections),
        vehicle_journeys=len(txc.VehicleJourneys),
        file_path=str(file_path),
        service_start_date=service_start_date,
        service_end_date=service_end_date,
        event_service=duration,
    )


def process_single_xml(file_info: zipfile.ZipInfo, config: WorkerConfig) -> None:
    """Process a single XML file and add it to the queue"""
    try:
        with config.zip_ref.open(file_info.filename) as xml_file:
            xml_data = xml_file.read()
            with BytesIO(xml_data) as xml_buffer:
                info = process_xml_file(
                    xml_file=xml_buffer,
                    filename=file_info.filename,
                    parent_zip=None,
                    tag_name=config.tag_name,
                    mode=config.mode,
                )
                config.xml_queue.put(info)
    except Exception:  # pylint: disable=broad-except
        log.error(
            "Error processing XML file", filename=file_info.filename, exc_info=True
        )
