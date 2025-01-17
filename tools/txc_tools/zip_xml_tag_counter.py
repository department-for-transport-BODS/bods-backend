"""
Search a Zip of XMLs for a Tag
"""

import concurrent.futures
import csv
import os
import queue
import threading
import zipfile
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Annotated, Iterator

import structlog
import typer
from lxml import etree
from pydantic import BaseModel, ConfigDict, Field

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ]
)
log = structlog.stdlib.get_logger()

app = typer.Typer()


class XMLTagInfo(BaseModel):
    """Pydantic model for XML tag count information"""

    model_config = ConfigDict(frozen=True)

    file_path: str = Field(..., description="Path to the XML file within the zip")
    tag_count: int = Field(
        ..., description="Number of occurrences of the specified tag"
    )
    parent_zip: str | None = Field(
        None, description="Name of the parent zip file if nested"
    )


class ZipTagStats(BaseModel):
    """Pydantic model for zip file tag statistics"""

    model_config = ConfigDict(frozen=True)

    zip_name: str = Field(..., description="Name of the zip file")
    file_count: int = Field(..., ge=0, description="Number of files containing the tag")
    total_tags: int = Field(..., description="Total number of tag occurrences")


def count_tags_in_xml(xml_data: bytes, tag_name: str) -> int:
    """Count occurrences of a specific tag in XML content"""
    try:
        root = etree.fromstring(xml_data)
        return len(root.findall(f".//{tag_name}", namespaces=root.nsmap))
    except Exception as e:  # pylint: disable=broad-except
        log.error("Error parsing XML", error=str(e))
        return 0


def process_xml_file(
    xml_file: BytesIO, filename: str, tag_name: str, parent_zip: str | None = None
) -> XMLTagInfo:
    """Process a single XML file and return its tag information"""
    xml_data = xml_file.read()
    log.debug(
        "Parsing and searching XML File", filename=filename, parent_zip=parent_zip
    )
    count = count_tags_in_xml(xml_data, tag_name)
    return XMLTagInfo(file_path=filename, tag_count=count, parent_zip=parent_zip)


def process_nested_zip(
    nested_zip_data: bytes, parent_zip_name: str, tag_name: str
) -> list[XMLTagInfo]:
    """Process a nested zip file, returning tag count information"""
    results: list[XMLTagInfo] = []
    with BytesIO(nested_zip_data) as zip_buffer:
        with zipfile.ZipFile(zip_buffer) as nested_zip_ref:
            for nested_file in nested_zip_ref.filelist:
                if nested_file.filename.endswith(".xml"):
                    try:
                        with nested_zip_ref.open(nested_file.filename) as xml_file:
                            xml_data = xml_file.read()
                            with BytesIO(xml_data) as xml_buffer:
                                info = process_xml_file(
                                    xml_buffer,
                                    nested_file.filename,
                                    tag_name,
                                    parent_zip_name,
                                )
                                if info.tag_count > 0:
                                    results.append(info)
                    except Exception as e:  # pylint: disable=broad-except
                        log.error(
                            "Error processing XML in nested zip",
                            filename=nested_file.filename,
                            parent_zip=parent_zip_name,
                            error=str(e),
                        )
    return results


def calculate_zip_stats(xml_files: list[XMLTagInfo]) -> dict[str, ZipTagStats]:
    """Calculate statistics for each zip file"""
    stats: dict[str, dict] = defaultdict(lambda: {"file_count": 0, "total_tags": 0})

    for xml_file in xml_files:
        zip_name = xml_file.parent_zip if xml_file.parent_zip else "root"
        stats[zip_name]["file_count"] += 1
        stats[zip_name]["total_tags"] += xml_file.tag_count

    return {
        zip_name: ZipTagStats(
            zip_name=zip_name,
            file_count=data["file_count"],
            total_tags=data["total_tags"],
        )
        for zip_name, data in stats.items()
    }


def process_single_xml(
    zip_ref: zipfile.ZipFile,
    file_info: zipfile.ZipInfo,
    tag_name: str,
    xml_queue: queue.Queue,
) -> None:
    """Process a single XML file and add it to the queue"""
    try:
        with zip_ref.open(file_info.filename) as xml_file:
            xml_data = xml_file.read()
            with BytesIO(xml_data) as xml_buffer:
                info = process_xml_file(xml_buffer, file_info.filename, tag_name)
                if info.tag_count > 0:
                    xml_queue.put(info)
    except Exception as e:  # pylint: disable=broad-except
        log.error(
            "Error processing XML file",
            filename=file_info.filename,
            error=str(e),
        )


def process_single_nested_zip(
    zip_ref: zipfile.ZipFile,
    file_info: zipfile.ZipInfo,
    tag_name: str,
    executor: concurrent.futures.ThreadPoolExecutor,
    future_queue: queue.Queue,
) -> None:
    """Process a single nested ZIP file and add its future to the queue"""
    try:
        log.info("Processing Sub Zip File", filename=file_info.filename)
        with zip_ref.open(file_info.filename) as nested_zip:
            nested_zip_data = nested_zip.read()
            future = executor.submit(
                process_nested_zip,
                nested_zip_data,
                file_info.filename,
                tag_name,
            )
            future_queue.put(future)
    except Exception as e:  # pylint: disable=broad-except
        log.error(
            "Error processing nested zip",
            filename=file_info.filename,
            error=str(e),
        )


def process_file_worker(
    zip_ref: zipfile.ZipFile,
    file_list: list[zipfile.ZipInfo],
    tag_name: str,
    xml_queue: queue.Queue,
    future_queue: queue.Queue,
    executor: concurrent.futures.ThreadPoolExecutor,
) -> None:
    """Worker function to process files from the zip"""
    while True:
        try:
            file_info = file_list.pop(0)
        except IndexError:
            break

        if file_info.filename.endswith(".xml"):
            process_single_xml(zip_ref, file_info, tag_name, xml_queue)
        elif file_info.filename.endswith(".zip"):
            process_single_nested_zip(
                zip_ref, file_info, tag_name, executor, future_queue
            )


def handle_futures_and_queues(
    processing_thread: threading.Thread,
    future_queue: queue.Queue,
    xml_queue: queue.Queue,
) -> Iterator[XMLTagInfo]:
    """Handle futures and queues to yield XML tag information"""
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
                future: concurrent.futures.Future[list[XMLTagInfo]] = (
                    future_queue.get_nowait()
                )
            except queue.Empty:
                break
            else:
                try:
                    results = future.result()
                    yield from results
                except Exception as e:  # pylint: disable=broad-except
                    log.error("Error processing sub-zip", error=str(e))

        if processing_thread.is_alive():
            threading.Event().wait(0.1)


def process_zip_contents(
    zip_path: str, tag_name: str, max_workers: int = 4
) -> Iterator[XMLTagInfo]:
    """Process contents of a zip file with parallel sub-zip processing"""
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            log.info("Files in Zip", count=len(zip_ref.filelist))

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers
            ) as executor:
                future_queue: queue.Queue = queue.Queue()
                xml_queue: queue.Queue = queue.Queue()

                # Start processing thread
                processing_thread = threading.Thread(
                    target=process_file_worker,
                    args=(
                        zip_ref,
                        zip_ref.filelist,
                        tag_name,
                        xml_queue,
                        future_queue,
                        executor,
                    ),
                )
                processing_thread.start()

                # Handle queues and yield results
                yield from handle_futures_and_queues(
                    processing_thread, future_queue, xml_queue
                )

                processing_thread.join()

    except zipfile.BadZipFile:
        log.error("Error processing zip file BadZipFile", zip_path=zip_path)
    except Exception as e:  # pylint: disable=broad-except
        log.error("Error processing zip file", zip_path=zip_path, error=str(e))


def write_detailed_report(
    sorted_xml_files: list[XMLTagInfo], detailed_path: Path
) -> None:
    """Write detailed tag count report to CSV"""
    with open(detailed_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Parent Zip", "File Path", "Tag Count"])
        for xml_file in sorted_xml_files:
            writer.writerow(
                [
                    xml_file.parent_zip or "",
                    xml_file.file_path,
                    xml_file.tag_count,
                ]
            )


def write_stats_report(sorted_stats: list[ZipTagStats], stats_path: Path) -> None:
    """Write zip statistics report to CSV"""
    with open(stats_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "Zip Names",
                "Number of Files with Tag",
                "Total Tag Occurrences",
            ]
        )
        for stat in sorted_stats:
            writer.writerow(
                [
                    stat.zip_name,
                    stat.file_count,
                    stat.total_tags,
                ]
            )


def write_csv_reports(
    tag_name: str, xml_files: list[XMLTagInfo], base_path: Path
) -> None:
    """Write both detailed tag report and zip statistics report, sorted by count"""
    # Sort XML files by tag count in descending order
    sorted_xml_files = sorted(xml_files, key=lambda x: x.tag_count, reverse=True)

    # Write detailed tag report
    detailed_path = base_path.with_name(f"{base_path.stem}_{tag_name}_detailed.csv")
    write_detailed_report(sorted_xml_files, detailed_path)

    # Calculate and write zip statistics
    stats = calculate_zip_stats(xml_files)
    sorted_stats = sorted(stats.values(), key=lambda x: x.total_tags, reverse=True)
    stats_path = base_path.with_name(f"{base_path.stem}_{tag_name}_stats.csv")
    write_stats_report(sorted_stats, stats_path)

    log.info(
        "CSV reports generated", detailed_path=detailed_path, stats_path=stats_path
    )


def process_zip_file_parallel(
    zip_path: str, tag_name: str, sub_zip_workers: int = 4
) -> None:
    """Process a zip file and generate both detailed and summary reports"""
    if not os.path.exists(zip_path):
        log.error("Input file not found", zip_path=zip_path)
        return

    log.info(
        "Processing ZIP File",
        zip_path=zip_path,
        tag_name=tag_name,
        sub_zip_workers=sub_zip_workers,
    )

    xml_files = list(
        process_zip_contents(zip_path, tag_name, max_workers=sub_zip_workers)
    )

    # Generate reports
    output_path = Path(zip_path).with_suffix(".csv")
    write_csv_reports(tag_name, xml_files, output_path)


@app.command()
def analyze_tags(
    zip_files: Annotated[
        list[Path],
        typer.Argument(
            help="One or more zip files to process",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    tag_name: Annotated[
        str,
        typer.Argument(help="XML tag name to search for"),
    ],
    sub_zip_workers: Annotated[
        int,
        typer.Option(
            "--sub-zip-workers",
            "-w",
            help="Number of worker threads for processing sub-zips",
            min=1,
            max=16,
            show_default=True,
        ),
    ] = 4,
) -> None:
    """
    Process multiple ZIP files in parallel, counting occurrences of specified XML tags
    and generating CSV reports.
    """
    log.info(
        "Starting Processing",
        zip_files=zip_files,
        tag_name=tag_name,
        sub_zip_workers=sub_zip_workers,
    )
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # Create futures and wait for them to complete
        futures = [
            executor.submit(
                process_zip_file_parallel, str(zip_path), tag_name, sub_zip_workers
            )
            for zip_path in zip_files
        ]
        # Wait for all futures to complete and handle any exceptions
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:  # pylint: disable=broad-except
                log.error("Error processing zip file", error=str(e))


if __name__ == "__main__":
    app()
