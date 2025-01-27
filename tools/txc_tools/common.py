"""
Module defines helper functions for TxC tools
"""

import concurrent.futures
import os
import queue
import threading
import zipfile
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Iterator, Union

import structlog
from common_layer.txc.models.txc_data import TXCData
from common_layer.txc.models.txc_stoppoint import TXCStopPoint
from common_layer.txc.parser.parser_txc import load_xml_data, parse_txc_from_element
from pydantic import BaseModel

from .csv_output import write_csv_reports
from .models import AnalysisMode, WorkerConfig, XMLFileInfo, XMLTagInfo, XmlTxcInventory
from .utils import count_tags_in_xml, get_size_mb

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ]
)

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


def get_tag_size_object(**kwargs: dict[str, Any]) -> Union[XMLFileInfo, XMLTagInfo]:
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
    AnalysisMode, Callable[..., Union[XMLFileInfo, XMLTagInfo, XmlTxcInventory]]
] = {
    AnalysisMode.SIZE: get_tag_size_object,
    AnalysisMode.TAG: get_tag_size_object,
    AnalysisMode.TXC: get_txc_object,
}


def process_xml_file(**kwargs) -> Union[XMLFileInfo, XMLTagInfo, XmlTxcInventory]:
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


def generate_txc_row_data(
    txc: TXCData, file_path: Union[Path, BytesIO]
) -> XmlTxcInventory:
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


def process_single_nested_zip(file_info: zipfile.ZipInfo, config: WorkerConfig) -> None:
    """Process a single nested ZIP file and add its future to the queue"""
    try:
        log.info("Processing Sub Zip File", filename=file_info.filename)
        with config.zip_ref.open(file_info.filename) as nested_zip:
            nested_zip_data = nested_zip.read()
            future = config.executor.submit(
                process_nested_zip,
                nested_zip_data,
                file_info.filename,
                config.mode,
                config.tag_name,
            )
            config.future_queue.put(future)
    except Exception:  # pylint: disable=broad-except
        log.error(
            "Error processing nested zip", filename=file_info.filename, exc_info=True
        )


def process_nested_zip(
    nested_zip_data: bytes,
    parent_zip_name: str,
    mode: AnalysisMode,
    tag_name: str | None = None,
) -> list[BaseModel]:
    """Process a nested zip file, returning XML file information"""
    results: list[BaseModel] = []
    with BytesIO(nested_zip_data) as zip_buffer:
        with zipfile.ZipFile(zip_buffer) as nested_zip_ref:
            for nested_file in nested_zip_ref.filelist:
                if nested_file.filename.endswith(".xml"):
                    try:
                        with nested_zip_ref.open(nested_file.filename) as xml_file:
                            xml_data = xml_file.read()
                            with BytesIO(xml_data) as xml_buffer:
                                info = process_xml_file(
                                    xml_file=xml_buffer,
                                    filename=nested_file.filename,
                                    parent_zip=parent_zip_name,
                                    tag_name=tag_name,
                                    mode=mode,
                                )
                                results.append(info)
                    except Exception as e:  # pylint: disable=broad-except
                        log.error(
                            "Error processing XML in nested zip",
                            filename=nested_file.filename,
                            parent_zip=parent_zip_name,
                            error=str(e),
                        )
    return results


def process_file_worker(config: WorkerConfig) -> None:
    """Worker function to process files from the zip"""
    while True:
        try:
            file_info = config.file_list.pop(0)
        except IndexError:
            break

        if file_info.filename.endswith(".xml"):
            process_single_xml(
                file_info,
                config,
            )
        elif file_info.filename.endswith(".zip"):
            process_single_nested_zip(file_info, config)


def handle_futures_and_queues(
    processing_thread: threading.Thread,
    future_queue: queue.Queue,
    xml_queue: queue.Queue,
) -> Iterator[XMLFileInfo | XMLTagInfo]:
    """Handle futures and queues to yield XML file information"""
    while (
        processing_thread.is_alive()
        or not future_queue.empty()
        or not xml_queue.empty()
    ):
        # Process XML queue
        while True:
            try:
                yield xml_queue.get_nowait()
            except queue.Empty:
                break

        # Process future queue
        while True:
            try:
                future: concurrent.futures.Future[list[XMLFileInfo | XMLTagInfo]] = (
                    future_queue.get_nowait()
                )
            except queue.Empty:
                break
            else:
                try:
                    results = future.result()
                    yield from results
                except Exception:  # pylint: disable=broad-except
                    log.error("Error processing sub-zip", exc_info=True)

        if processing_thread.is_alive():
            threading.Event().wait(0.1)


def process_zip_contents(
    zip_path: str,
    max_workers: int,
    mode: AnalysisMode,
    tag_name: str | None = None,
) -> Iterator[XMLFileInfo | XMLTagInfo]:
    """Process contents of a zip file with parallel sub-zip processing"""
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            log.info("Files in Zip", count=len(zip_ref.filelist))

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers
            ) as executor:
                future_queue: queue.Queue = queue.Queue()
                xml_queue: queue.Queue = queue.Queue()

                config = WorkerConfig(
                    zip_ref=zip_ref,
                    file_list=zip_ref.filelist,
                    xml_queue=xml_queue,
                    future_queue=future_queue,
                    executor=executor,
                    mode=mode,
                    tag_name=tag_name,
                )

                # Start processing thread
                processing_thread = threading.Thread(
                    target=process_file_worker,
                    args=(config,),
                )
                processing_thread.start()

                # Handle queues and yield results
                yield from handle_futures_and_queues(
                    processing_thread, future_queue, xml_queue
                )

                processing_thread.join()

    except zipfile.BadZipFile:
        log.error("Error processing zip file BadZipFile", zip_path=zip_path)
    except Exception:  # pylint: disable=broad-except
        log.error("Error processing zip file", zip_path=zip_path, exc_info=True)


def process_zip_file_parallel(
    zip_path: str,
    mode: AnalysisMode,
    tag_name: str | None = None,
    sub_zip_workers: int = 4,
) -> None:
    """Process a zip file and generate both detailed and summary reports"""
    if not os.path.exists(zip_path):
        log.error("Input file not found", zip_path=zip_path)
        raise FileNotFoundError(zip_path)

    log.info(
        "Processing ZIP File",
        zip_path=zip_path,
        mode=mode,
        tag_name=tag_name,
        sub_zip_workers=sub_zip_workers,
    )
    xml_files: list[BaseModel] = list(  # type: ignore
        process_zip_contents(
            zip_path,
            max_workers=sub_zip_workers,
            mode=mode,
            tag_name=tag_name,
        )
    )
    # Generate reports
    report_args = {
        "xml_files": xml_files,
        "base_path": Path(zip_path).with_suffix(".csv"),
        "mode": mode,
        "tag_name": tag_name,
    }
    write_csv_reports(**report_args)


def execute_process(
    zip_files: list[Path],
    mode: AnalysisMode,
    tag_name: str | None = None,
    sub_zip_workers: int = 4,
) -> None:
    """
    Launch process for xml file parsing and extracting datas
    """
    log.info(
        "Starting Processing",
        zip_files=zip_files,
        mode=mode,
        tag_name=tag_name,
        sub_zip_workers=sub_zip_workers,
    )
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # Create futures and wait for them to complete
        futures = [
            executor.submit(
                process_zip_file_parallel,
                str(zip_path),
                mode,
                tag_name,
                sub_zip_workers,
            )
            for zip_path in zip_files
        ]
        # Wait for all futures to complete and handle any exceptions
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception:  # pylint: disable=broad-except
                log.error("Error processing zip file", exc_info=True)
