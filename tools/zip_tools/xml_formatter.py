"""
Remove Whitespace from XMLs in a Zip and generate new zip
"""

import concurrent.futures
import os
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Annotated

import typer
from pydantic import BaseModel
from structlog.stdlib import get_logger

log = get_logger()


class XmlFile(BaseModel):
    """Represents an XML file to be processed."""

    relative_path: str
    absolute_path: Path
    processed_content: bytes | None = None


class ProcessingResult(BaseModel):
    """Represents the result of processing XML files."""

    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    success_rate: float = 0.0
    processing_time: float = 0.0


def extract_zip(zip_path: Path, extract_to: Path) -> int:
    """Extract all files from a zip file to a directory."""
    log.info("Extracting zip file", zip_path=str(zip_path), extract_to=str(extract_to))
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        file_count = len(zip_ref.namelist())
        zip_ref.extractall(extract_to)
    log.info("Extraction complete", zip_path=str(zip_path), file_count=file_count)
    return file_count


def collect_xml_files(base_dir: Path) -> list[XmlFile]:
    """Collect all XML files from the directory structure."""
    log.info("Collecting XML files", base_dir=str(base_dir))
    xml_files: list[XmlFile] = []

    for root, _, files in os.walk(base_dir):
        root_path = Path(root)
        for file in files:
            if file.lower().endswith(".xml"):
                abs_path = root_path / file
                # Make the path relative to the base_dir
                rel_path = abs_path.relative_to(base_dir)
                xml_files.append(
                    XmlFile(relative_path=str(rel_path), absolute_path=abs_path)
                )

    log.info("XML files collected", file_count=len(xml_files))
    return xml_files


def process_xml_file(xml_file: XmlFile) -> XmlFile:
    """Process a single XML file with xmllint to remove whitespace."""
    try:
        result = subprocess.run(
            ["xmllint", "--noblanks", str(xml_file.absolute_path)],
            capture_output=True,
            check=True,
            text=False,  # We want bytes output
        )

        xml_file.processed_content = result.stdout
        return xml_file

    except subprocess.CalledProcessError as e:
        log.error(
            "Failed to process XML file",
            file=str(xml_file.absolute_path),
            error=str(e),
            stderr=e.stderr.decode("utf-8", errors="replace") if e.stderr else None,
        )
        # Return the original file but with None as processed_content to indicate failure
        xml_file.processed_content = None
        return xml_file
    except Exception as e:  # pylint: disable=broad-exception-caught
        log.error(
            "Unexpected error processing XML file",
            file=str(xml_file.absolute_path),
            error=str(e),
        )
        xml_file.processed_content = None
        return xml_file


def process_files_parallel(
    xml_files: list[XmlFile], max_workers: int | None = None
) -> tuple[ProcessingResult, list[XmlFile]]:
    """Process XML files in parallel using ThreadPoolExecutor."""
    total_files = len(xml_files)
    log.info(
        "Starting parallel processing", total_files=total_files, max_workers=max_workers
    )

    result = ProcessingResult(total_files=total_files)
    start_time = time.time()

    processed_files: list[XmlFile] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(process_xml_file, xml_file): xml_file
            for xml_file in xml_files
        }

        # Process as they complete
        for i, future in enumerate(concurrent.futures.as_completed(future_to_file), 1):
            xml_file = future_to_file[future]
            try:
                processed_file = future.result()
                processed_files.append(processed_file)

                if i % 1000 == 0 or i == total_files:
                    log.info(
                        "Processing progress",
                        completed=i,
                        total=total_files,
                        percent=f"{(i/total_files)*100:.1f}%",
                    )

            except Exception as e:  # pylint: disable=broad-exception-caught
                log.error(
                    "Error getting result",
                    file=str(xml_file.absolute_path),
                    error=str(e),
                )
                result.failed_files += 1

    # Count successes
    success_count = sum(
        1 for file in processed_files if file.processed_content is not None
    )
    result.processed_files = success_count
    result.failed_files = total_files - success_count
    result.success_rate = (success_count / total_files) if total_files > 0 else 0
    result.processing_time = time.time() - start_time

    log.info(
        "Parallel processing complete",
        total=result.total_files,
        processed=result.processed_files,
        failed=result.failed_files,
        success_rate=f"{result.success_rate*100:.2f}%",
        processing_time=f"{result.processing_time:.2f}s",
    )

    return result, processed_files


def create_lzma_zip(output_path: Path, xml_files: list[XmlFile]) -> None:
    """Create a new LZMA-compressed zip file with the processed XML files."""
    log.info("Creating LZMA-compressed zip file", output_path=str(output_path))

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_LZMA) as zip_out:
        for xml_file in xml_files:
            if xml_file.processed_content is not None:
                log.debug("Adding XML to zip", xml_file=xml_file.relative_path)
                zip_out.writestr(xml_file.relative_path, xml_file.processed_content)

    log.info(
        "LZMA zip creation complete",
        output_path=str(output_path),
        file_count=len(xml_files),
    )


def determine_optimal_workers() -> int:
    """Determine the optimal number of worker threads based on system resources."""
    cpu_count = os.cpu_count() or 1
    return cpu_count * 4


def process_zip_file(
    input_zip_path: Path, output_zip_path: Path, max_workers: int | None = None
) -> ProcessingResult:
    """Process a zip file to format XML files and repackage them."""
    log.info(
        "Starting zip processing",
        input_zip=str(input_zip_path),
        output_zip=str(output_zip_path),
        max_workers=max_workers,
    )

    if max_workers is None:
        max_workers = determine_optimal_workers()
        log.info("Using automatic worker count", max_workers=max_workers)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        extract_zip(input_zip_path, temp_path)

        xml_files = collect_xml_files(temp_path)

        result, processed_files = process_files_parallel(xml_files, max_workers)

        successful_files = [
            file for file in processed_files if file.processed_content is not None
        ]

        create_lzma_zip(output_zip_path, successful_files)

    log.info(
        "Zip processing complete",
        input_zip=str(input_zip_path),
        output_zip=str(output_zip_path),
        processing_result={
            "total_files": result.total_files,
            "processed_files": result.processed_files,
            "failed_files": result.failed_files,
            "success_rate": f"{result.success_rate*100:.2f}%",
            "processing_time": f"{result.processing_time:.2f}s",
        },
    )

    return result


def main(input_zip: str, output_zip: str, workers: int | None = None) -> None:
    """Main function to process a zip file."""
    input_path = Path(input_zip)
    output_path = Path(output_zip)

    if not input_path.exists():
        log.error("Input zip file does not exist", input_zip=input_zip)
        sys.exit(1)

    start_time = time.time()
    log.info(
        "Starting XML formatting process", input_zip=input_zip, output_zip=output_zip
    )

    result = process_zip_file(input_path, output_path, workers)

    total_time = time.time() - start_time
    log.info(
        "XML formatting process complete",
        input_zip=input_zip,
        output_zip=output_zip,
        total_time=f"{total_time:.2f}s",
        processing_result={
            "total_files": result.total_files,
            "processed_files": result.processed_files,
            "failed_files": result.failed_files,
            "success_rate": f"{result.success_rate*100:.2f}%",
            "processing_time": f"{result.processing_time:.2f}s",
        },
    )


def reformat(
    input_zip: Annotated[str, typer.Argument(help="Path to the input zip file")],
    output_zip: Annotated[
        str, typer.Argument(help="Path to the output LZMA-compressed zip file")
    ],
    workers: Annotated[
        int | None,
        typer.Option(
            "--workers",
            help="Maximum number of worker threads (default: auto-determined)",
        ),
    ] = None,
) -> None:
    """Process XML files in a zip to remove whitespace using xmllint."""
    input_path = Path(input_zip)
    output_path = Path(output_zip)

    if not input_path.exists():
        log.error("Input zip file does not exist", input_zip=input_zip)
        sys.exit(1)

    log.info(
        "Starting zip file processing",
        input_zip=input_zip,
        output_zip=output_zip,
        workers=workers,
    )
    process_zip_file(input_path, output_path, workers)
    log.info("Zip file processing complete", input_zip=input_zip, output_zip=output_zip)


if __name__ == "__main__":
    typer.run(reformat)
