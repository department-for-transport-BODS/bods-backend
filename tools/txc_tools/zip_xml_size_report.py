"""
Searches through a Zip for nested zips and generates a report of XMLs and their sizes
"""

import concurrent.futures
import csv
import os
import queue
import threading
import zipfile
from collections import defaultdict
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import IO, Annotated, Iterator

import structlog
import typer
from pydantic import BaseModel, ConfigDict, Field, computed_field

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ]
)
log = structlog.stdlib.get_logger()

app = typer.Typer()


class XMLFileInfo(BaseModel):
    """Pydantic model for XML file information"""

    model_config = ConfigDict(frozen=True)

    file_path: str = Field(..., description="Path to the XML file within the zip")
    size_mb: Decimal = Field(
        ..., description="Size of the XML file in megabytes", decimal_places=2
    )
    parent_zip: str | None = Field(
        None, description="Name of the parent zip file if nested"
    )


class ZipStats(BaseModel):
    """Pydantic model for zip file statistics"""

    model_config = ConfigDict(frozen=True)

    zip_name: str = Field(..., description="Name of the zip file")
    file_count: int = Field(..., ge=0, description="Number of XML files in the zip")
    total_size_mb: Decimal = Field(
        ..., description="Total size of all XMLs in megabytes", decimal_places=2
    )

    @computed_field
    def avg_file_size_mb(self) -> Decimal:
        """Average size of XML files in the zip"""
        if self.file_count == 0:
            return Decimal("0")
        return (self.total_size_mb / self.file_count).quantize(Decimal("0.01"))


def get_size_mb(file_obj: IO[bytes]) -> Decimal:
    """Calculate file size in megabytes using constant memory"""
    chunk_size = 8192  # 8KB chunks
    total_size = 0

    while chunk := file_obj.read(chunk_size):
        total_size += len(chunk)

    file_obj.seek(0)  # Reset file pointer
    return Decimal(str(total_size / (1024 * 1024))).quantize(Decimal("0.01"))


def process_xml_file(
    xml_file: IO[bytes], filename: str, parent_zip: str | None = None
) -> XMLFileInfo:
    """Process a single XML file and return its information"""
    return XMLFileInfo(
        file_path=filename, size_mb=get_size_mb(xml_file), parent_zip=parent_zip
    )


def process_nested_zip(
    nested_zip_data: bytes, parent_zip_name: str
) -> list[XMLFileInfo]:
    """Process a nested zip file, returning XML file information"""
    results: list[XMLFileInfo] = []
    with BytesIO(nested_zip_data) as zip_buffer:
        with zipfile.ZipFile(zip_buffer) as nested_zip_ref:
            for nested_file in nested_zip_ref.filelist:
                if nested_file.filename.endswith(".xml"):
                    try:
                        with nested_zip_ref.open(nested_file.filename) as xml_file:
                            xml_data = xml_file.read()
                            with BytesIO(xml_data) as xml_buffer:
                                results.append(
                                    process_xml_file(
                                        xml_buffer,
                                        nested_file.filename,
                                        parent_zip_name,
                                    )
                                )
                    except Exception as e:
                        log.error(
                            "Error processing XML in nested zip",
                            filename=nested_file.filename,
                            parent_zip=parent_zip_name,
                            error=str(e),
                        )
    return results


def calculate_zip_stats(xml_files: list[XMLFileInfo]) -> dict[str, ZipStats]:
    """Calculate statistics for each zip file"""
    stats: dict[str, dict] = defaultdict(
        lambda: {"count": 0, "total_size": Decimal("0")}
    )

    for xml_file in xml_files:
        zip_name = xml_file.parent_zip if xml_file.parent_zip else "root"
        stats[zip_name]["count"] += 1
        stats[zip_name]["total_size"] += xml_file.size_mb

    return {
        zip_name: ZipStats(
            zip_name=zip_name,
            file_count=data["count"],
            total_size_mb=data["total_size"].quantize(Decimal("0.01")),
        )
        for zip_name, data in stats.items()
    }


def process_single_xml(
    zip_ref: zipfile.ZipFile, file_info: zipfile.ZipInfo, xml_queue: queue.Queue
) -> None:
    """Process a single XML file and add it to the queue"""
    try:
        with zip_ref.open(file_info.filename) as xml_file:
            xml_data = xml_file.read()
            with BytesIO(xml_data) as xml_buffer:
                xml_queue.put(process_xml_file(xml_buffer, file_info.filename))
    except Exception:
        log.error(
            "Error processing XML file", filename=file_info.filename, exc_info=True
        )


def process_single_nested_zip(
    zip_ref: zipfile.ZipFile,
    file_info: zipfile.ZipInfo,
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
            )
            future_queue.put(future)
    except Exception:
        log.error(
            "Error processing nested zip", filename=file_info.filename, exc_info=True
        )


def process_file_worker(
    zip_ref: zipfile.ZipFile,
    file_list: list[zipfile.ZipInfo],
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
            process_single_xml(zip_ref, file_info, xml_queue)
        elif file_info.filename.endswith(".zip"):
            process_single_nested_zip(zip_ref, file_info, executor, future_queue)


def handle_futures_and_queues(
    processing_thread: threading.Thread,
    future_queue: queue.Queue,
    xml_queue: queue.Queue,
) -> Iterator[XMLFileInfo]:
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
                future: concurrent.futures.Future[list[XMLFileInfo]] = (
                    future_queue.get_nowait()
                )
            except queue.Empty:
                break
            else:
                try:
                    results = future.result()
                    yield from results
                except Exception:
                    log.error("Error processing sub-zip", exc_info=True)

        if processing_thread.is_alive():
            threading.Event().wait(0.1)


def process_zip_contents(zip_path: str, max_workers: int = 4) -> Iterator[XMLFileInfo]:
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
                    args=(zip_ref, zip_ref.filelist, xml_queue, future_queue, executor),
                )
                processing_thread.start()

                # Handle queues and yield results
                yield from handle_futures_and_queues(
                    processing_thread, future_queue, xml_queue
                )

                processing_thread.join()

    except zipfile.BadZipFile:
        log.error("Error processing zip file BadZipFile", zip_path=zip_path)


def write_detailed_report(
    sorted_xml_files: list[XMLFileInfo], detailed_path: Path
) -> None:
    """Write detailed XML report to CSV"""
    with open(detailed_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Parent Zip", "File Path", "Size (MB)"])
        for xml_file in sorted_xml_files:
            writer.writerow(
                [
                    xml_file.parent_zip or "",
                    xml_file.file_path,
                    str(xml_file.size_mb),
                ]
            )


def write_stats_report(sorted_stats: list[ZipStats], stats_path: Path) -> None:
    """Write zip statistics report to CSV"""
    with open(stats_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "Zip Names",
                "Number of Files in Zip",
                "Total Size of XMLs in Zip (MB)",
                "Average File Size (MB)",
            ]
        )
        for stat in sorted_stats:
            writer.writerow(
                [
                    stat.zip_name,
                    stat.file_count,
                    str(stat.total_size_mb),
                    str(stat.avg_file_size_mb),
                ]
            )


def write_csv_reports(xml_files: list[XMLFileInfo], base_path: Path) -> None:
    """Write both detailed XML report and zip statistics report, sorted by size"""
    # Sort XML files by size in descending order
    sorted_xml_files = sorted(xml_files, key=lambda x: x.size_mb, reverse=True)

    # Write detailed XML report
    detailed_path = base_path.with_name(f"{base_path.stem}_detailed.csv")
    write_detailed_report(sorted_xml_files, detailed_path)

    # Calculate and write zip statistics
    stats = calculate_zip_stats(xml_files)
    sorted_stats = sorted(stats.values(), key=lambda x: x.total_size_mb, reverse=True)
    stats_path = base_path.with_name(f"{base_path.stem}_stats.csv")
    write_stats_report(sorted_stats, stats_path)

    log.info(
        "CSV reports generated", detailed_path=detailed_path, stats_path=stats_path
    )


def process_zip_file_parallel(zip_path: str, sub_zip_workers: int = 4) -> None:
    """Process a zip file and generate both detailed and summary reports"""
    if not os.path.exists(zip_path):
        log.error("Input file not found", zip_path=zip_path)
        return

    log.info(
        "Processing ZIP File",
        zip_path=zip_path,
        sub_zip_workers=sub_zip_workers,
    )

    xml_files = list(process_zip_contents(zip_path, max_workers=sub_zip_workers))

    # Generate reports
    output_path = Path(zip_path).with_suffix(".csv")
    write_csv_reports(xml_files, output_path)


@app.command()
def analyze_zips(
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
    Process multiple ZIP files in parallel, analyzing their XML contents and generating CSV reports.
    """
    log.info(
        "Starting Processing", zip_files=zip_files, sub_zip_workers=sub_zip_workers
    )
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # Create futures and wait for them to complete
        futures = [
            executor.submit(process_zip_file_parallel, str(zip_path), sub_zip_workers)
            for zip_path in zip_files
        ]
        # Wait for all futures to complete and handle any exceptions
        for future in concurrent.futures.as_completed(futures):
            future.result()


if __name__ == "__main__":
    app()
