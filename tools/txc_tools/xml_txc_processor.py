"""
Module to support the functionality of TxC report inventory
"""

from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any, Union

from common_layer.txc.models.txc_data import TXCData
from common_layer.txc.models.txc_stoppoint import TXCStopPoint
from common_layer.txc.parser.parser_txc import load_xml_data, parse_txc_from_element

from .common import log
from .models import XMLTxCInventory


def generate_txc_row_data(
    txc: TXCData, file_path: Union[Path, BytesIO]
) -> XMLTxCInventory:
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

    return XMLTxCInventory(
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


def get_txc_object(**kwargs: dict[str, Any]) -> XMLTxCInventory:
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
