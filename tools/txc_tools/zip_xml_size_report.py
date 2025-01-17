"""
Script to analyze XML files within nested zip files and generate a CSV report.
Handles single level of zip nesting and processes files in parallel.
"""

import concurrent.futures
import contextlib
import csv
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Iterator

import structlog

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ]
)
log = structlog.stdlib.get_logger()


@dataclass
class XMLFileInfo:
    """Data class to store XML file information."""

    file_path: str
    size_mb: float
    parent_zip: str | None = None


def get_size_mb(file_obj: IO[bytes]) -> float:
    """Calculate file size in megabytes using constant memory."""
    chunk_size = 8192  # 8KB chunks
    total_size = 0

    while chunk := file_obj.read(chunk_size):
        total_size += len(chunk)

    file_obj.seek(0)  # Reset file pointer
    return total_size / (1024 * 1024)


def process_xml_file(
    xml_file: IO[bytes], filename: str, parent_zip: str | None = None
) -> XMLFileInfo:
    """Process a single XML file and return its information."""
    return XMLFileInfo(
        file_path=filename, size_mb=get_size_mb(xml_file), parent_zip=parent_zip
    )


def process_nested_zip(
    nested_zip_file: IO[bytes], parent_zip_name: str
) -> Iterator[XMLFileInfo]:
    """Process a nested zip file, yielding XML file information."""
    with contextlib.closing(zipfile.ZipFile(nested_zip_file)) as nested_zip_ref:
        for nested_file in nested_zip_ref.filelist:
            if nested_file.filename.endswith(".xml"):
                try:
                    with nested_zip_ref.open(nested_file.filename) as xml_file:
                        yield process_xml_file(
                            xml_file, nested_file.filename, parent_zip_name
                        )
                except Exception as e:  # pylint: disable=broad-exception-caught
                    log.error(
                        "Error processing XML in nested zip",
                        filename=nested_file.filename,
                        parent_zip=parent_zip_name,
                        error=str(e),
                    )


def process_zip_contents(zip_path: str) -> Iterator[XMLFileInfo]:
    """
    Process contents of a zip file, yielding XML file information using streaming approach.
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            log.info("Files in Zip", count=len(zip_ref.filelist))
            for file_info in zip_ref.filelist:

                try:
                    if file_info.filename.endswith(".xml"):
                        with zip_ref.open(file_info.filename) as xml_file:
                            yield process_xml_file(xml_file, file_info.filename)

                    elif file_info.filename.endswith(".zip"):
                        log.info("Processing Sub Zip File", filename=file_info.filename)
                        with zip_ref.open(file_info.filename) as nested_zip:
                            yield from process_nested_zip(
                                nested_zip, file_info.filename
                            )

                except Exception as e:  # pylint: disable=broad-exception-caught
                    log.error(
                        "Error processing file in zip",
                        filename=file_info.filename,
                        error=str(e),
                    )
                    continue

    except zipfile.BadZipFile:
        log.error("Error processing zip file", zip_path=zip_path)


def write_csv_streaming(xml_files: Iterator[XMLFileInfo], output_path: Path) -> int:
    """
    Write XML file information to CSV using streaming approach.
    Returns the total number of files written.
    """
    total_files = 0
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Parent Zip", "File Path", "Size (MB)"])

        for xml_file in xml_files:
            writer.writerow(
                [
                    xml_file.parent_zip or "",
                    xml_file.file_path,
                    f"{xml_file.size_mb:.2f}",
                ]
            )
            total_files += 1

    return total_files


def process_zip_file_parallel(zip_path: str) -> None:
    """
    Process a zip file and its contents, generating a CSV report with optimized memory usage.
    """
    if not os.path.exists(zip_path):
        log.error("Input file not found", zip_path=zip_path)
        return
    output_path = Path(zip_path).with_suffix(".csv")
    log.info("Processing ZIP Files", zip_path=zip_path, output_path=output_path)
    total_files = write_csv_streaming(process_zip_contents(zip_path), output_path)
    log.info("CSV report generated", path=output_path, total_xml_files=total_files)


def main():
    """Main entry point of the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze XML files in nested zip files and generate a CSV report."
    )
    parser.add_argument("zip_files", nargs="+", help="One or more zip files to process")

    args = parser.parse_args()

    # Process multiple zip files in parallel
    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(process_zip_file_parallel, args.zip_files)


if __name__ == "__main__":
    main()
