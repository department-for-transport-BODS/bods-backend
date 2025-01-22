"""
Module defines helper functions for TxC tools
"""

import concurrent.futures
import queue
import threading
import zipfile
from collections import defaultdict
from decimal import Decimal
from io import BytesIO
from typing import IO, Iterator, Union

import structlog

from tools.txc_tools.models import AnalysisMode, WorkerConfig
from tools.txc_tools.utils import count_tags_in_xml, get_size_mb

from .models import XMLFileInfo, XMLTagInfo, ZipStats, ZipTagStats

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ]
)

log = structlog.stdlib.get_logger()


def process_xml_file(
    xml_file: Union[IO[bytes], BytesIO],
    filename: str,
    parent_zip: str | None = None,
    *,
    tag_name: str | None = None,
) -> Union[XMLFileInfo, XMLTagInfo]:
    """
    Process a single XML file and return its information (size or tag count).
    """
    xml_data = xml_file.read()
    xml_file.seek(0)
    if tag_name:
        log.debug(
            "Parsing and searching XML File", filename=filename, parent_zip=parent_zip
        )
        count = count_tags_in_xml(xml_data, tag_name)
        return XMLTagInfo(file_path=filename, tag_count=count, parent_zip=parent_zip)
    size_mb = get_size_mb(xml_file)
    return XMLFileInfo(file_path=filename, size_mb=size_mb, parent_zip=parent_zip)


def calculate_zip_stats(
    xml_files: list[XMLFileInfo] | list[XMLTagInfo], mode: AnalysisMode
) -> dict[str, ZipStats | ZipTagStats]:
    """Calculate statistics for each zip file"""
    stats: dict[str, dict] = defaultdict(
        lambda: {"file_count": 0, "total_size": Decimal("0"), "total_tags": 0}
    )

    for xml_file in xml_files:
        zip_name = xml_file.parent_zip if xml_file.parent_zip else "root"
        stats[zip_name]["file_count"] += 1
        if mode == AnalysisMode.SIZE and isinstance(xml_file, XMLFileInfo):
            stats[zip_name]["total_size"] += xml_file.size_mb
        elif mode == AnalysisMode.TAG and isinstance(xml_file, XMLTagInfo):
            stats[zip_name]["total_tags"] += xml_file.tag_count

    if mode == AnalysisMode.SIZE:
        return {
            zip_name: ZipStats(
                zip_name=zip_name,
                file_count=data["file_count"],
                total_size_mb=data["total_size"].quantize(Decimal("0.01")),
            )
            for zip_name, data in stats.items()
        }
    if mode == AnalysisMode.TAG:
        return {
            zip_name: ZipTagStats(
                zip_name=zip_name,
                file_count=data["file_count"],
                total_tags=data["total_tags"],
            )
            for zip_name, data in stats.items()
        }

    log.error("Unsupported analysis mode", mode=mode)
    raise ValueError("Invalid Analysis Mode")


def process_single_xml(file_info: zipfile.ZipInfo, config: WorkerConfig) -> None:
    """Process a single XML file and add it to the queue"""
    try:
        with config.zip_ref.open(file_info.filename) as xml_file:
            xml_data = xml_file.read()
            with BytesIO(xml_data) as xml_buffer:
                info = process_xml_file(
                    xml_buffer,
                    file_info.filename,
                    tag_name=config.tag_name,
                    parent_zip=None,
                )
                if (
                    config.mode == AnalysisMode.SIZE and isinstance(info, XMLFileInfo)
                ) or (
                    config.mode == AnalysisMode.TAG
                    and isinstance(info, XMLTagInfo)
                    and info.tag_count > 0
                ):
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
) -> list[XMLFileInfo | XMLTagInfo]:
    """Process a nested zip file, returning XML file information"""
    results: list[XMLFileInfo | XMLTagInfo] = []
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
                                )
                                if (
                                    mode == AnalysisMode.SIZE
                                    and isinstance(info, XMLFileInfo)
                                ) or (
                                    mode == AnalysisMode.TAG
                                    and isinstance(info, XMLTagInfo)
                                    and info.tag_count > 0
                                ):
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
