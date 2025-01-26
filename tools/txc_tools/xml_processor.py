"""
Module defines helper functions for TxC tools
"""

import concurrent.futures
import os
import queue
import threading
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Iterator, List, Optional, Union

from pydantic import BaseModel

from .calculation import count_tags_in_xml, get_size_mb
from .common import ReportMode, log
from .models import XMLFileInfo, XMLTagInfo, XMLTxCInventory
from .report import write_csv_reports
from .xml_txc_processor import get_txc_object


@dataclass
class WorkerConfig:
    """
    Worker configuration
    """

    zip_ref: zipfile.ZipFile
    file_list: list[zipfile.ZipInfo]
    xml_queue: queue.Queue
    future_queue: queue.Queue
    executor: concurrent.futures.ThreadPoolExecutor
    mode: ReportMode
    tag_name: Optional[str] = None


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
    if kwargs.get("mode") == ReportMode.TAG:
        count = count_tags_in_xml(xml_file.read(), tag_name)
        return XMLTagInfo(
            file_path=str(filename), tag_count=count, parent_zip=parent_zip
        )

    size_mb = get_size_mb(xml_file)
    return XMLFileInfo(file_path=str(filename), size_mb=size_mb, parent_zip=parent_zip)


XML_OBJECTS: dict[
    ReportMode, Callable[..., Union[XMLFileInfo, XMLTagInfo, XMLTxCInventory]]
] = {
    ReportMode.SIZE: get_tag_size_object,
    ReportMode.TAG: get_tag_size_object,
    ReportMode.TXC: get_txc_object,
}


def process_xml_file(**kwargs) -> Union[XMLFileInfo, XMLTagInfo, XMLTxCInventory]:
    """
    Process a single XML file and return its information (size or tag count).
    """
    mode = kwargs.get("mode")

    if not isinstance(mode, ReportMode):
        raise ValueError("mode must be an instance of ReportMode")

    xml_file = kwargs.get("xml_file")
    if not hasattr(xml_file, "read"):
        raise ValueError("xml_file must be a file-like object with a 'read' method")
    return XML_OBJECTS[mode](**kwargs)


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
    mode: ReportMode,
    tag_name: str | None = None,
) -> List[BaseModel]:
    """Process a nested zip file, returning XML file information"""
    results: List[BaseModel] = []
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
) -> Iterator[BaseModel]:
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
    mode: ReportMode,
    tag_name: str | None = None,
) -> Iterator[BaseModel]:
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
    mode: ReportMode,
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
    xml_files: List[BaseModel] = list(  # type: ignore
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
    mode: ReportMode,
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
