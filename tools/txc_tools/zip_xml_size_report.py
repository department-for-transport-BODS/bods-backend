"""
Searches through a Zip for nested zips and generates a report of XMLs and their sizes
"""

import concurrent.futures
import os
from pathlib import Path
from typing import List

from .common import log, process_zip_contents
from .csv_output import write_csv_reports
from .models import AnalysisMode, XMLFileInfo


def process_zip_file_parallel(zip_path: str, sub_zip_workers: int = 4) -> None:
    """Process a zip file and generate both detailed and summary reports"""
    if not os.path.exists(zip_path):
        log.error("Input file not found", zip_path=zip_path)
        raise FileNotFoundError(f"Input file not found {zip_path}")

    log.info(
        "Processing ZIP File",
        zip_path=zip_path,
        sub_zip_workers=sub_zip_workers,
    )
    xml_files: List[XMLFileInfo] = list(  # type: ignore
        process_zip_contents(
            zip_path, max_workers=sub_zip_workers, mode=AnalysisMode.SIZE
        )
    )

    # Generate reports
    output_path = Path(zip_path).with_suffix(".csv")
    write_csv_reports(
        xml_files=xml_files,  # type: ignore
        base_path=output_path,
        mode=AnalysisMode.SIZE,
    )


def analyze_zips(
    zip_files: list[Path],
    sub_zip_workers: int = 4,
) -> None:
    """
    Process multiple ZIP files in parallel, analyzing their XML contents and
    generating CSV reports.
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
