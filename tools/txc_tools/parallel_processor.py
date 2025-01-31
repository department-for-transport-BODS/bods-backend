"""
Module defines helper functions to process xml files parallel
"""

import concurrent.futures
import os
import queue
import threading
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Iterator

import structlog
from pydantic import BaseModel

from .csv_output import write_csv_reports
from .models import AnalysisMode, WorkerConfig, XmlTagLookUpInfo, XMLFileInfo, XMLTagInfo
from .xml_processor import process_single_xml, process_xml_file

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ]
)

log = structlog.stdlib.get_logger()


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
                config.lookup_info,
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
    lookup_info: XmlTagLookUpInfo | None = None,
) -> list[BaseModel]:
    """Process a nested zip file, returning XML file information"""
    results: list[BaseModel] = []
    log.info("process_nested_zip", lookup_info=lookup_info)
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
                                    mode=mode,
                                    lookup_info=lookup_info,
                                )
                                if isinstance(info, list):
                                    results.extend(info)
                                else:
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
    lookup_info: XmlTagLookUpInfo | None = None,
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
                    lookup_info=lookup_info,
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
    sub_zip_workers: int = 4,
    lookup_info: XmlTagLookUpInfo | None = None,
) -> None:
    """Process a zip file and generate both detailed and summary reports"""
    if not os.path.exists(zip_path):
        log.error("Input file not found", zip_path=zip_path)
        raise FileNotFoundError(zip_path)

    log.info(
        "Processing ZIP File",
        zip_path=zip_path,
        mode=mode,
        sub_zip_workers=sub_zip_workers,
        lookup_info=lookup_info,
    )
    xml_files: list[BaseModel] = list(  # type: ignore
        process_zip_contents(
            zip_path,
            max_workers=sub_zip_workers,
            mode=mode,
            lookup_info=lookup_info,
        )
    )

    log.info("process_zip_file_parallel", xml_files=xml_files)

    # Generate reports
    report_args = {
        "xml_files": xml_files,
        "base_path": Path(zip_path).with_suffix(".csv"),
        "mode": mode,
        "lookup_info": lookup_info,
    }
    write_csv_reports(**report_args)


def execute_process(
    zip_files: list[Path],
    mode: AnalysisMode,
    sub_zip_workers: int = 4,
    lookup_info: XmlTagLookUpInfo | None = None,
) -> None:
    """
    Launch process for xml file parsing and extracting datas
    """
    log.info(
        "Starting Processing",
        zip_files=zip_files,
        mode=mode,
        lookup_info=lookup_info,
        sub_zip_workers=sub_zip_workers,
    )
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # Create futures and wait for them to complete
        futures = [
            executor.submit(
                process_zip_file_parallel,
                str(zip_path),
                mode,
                sub_zip_workers,
                lookup_info,
            )
            for zip_path in zip_files
        ]
        # Wait for all futures to complete and handle any exceptions
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception:  # pylint: disable=broad-except
                log.error("Error processing zip file", exc_info=True)
