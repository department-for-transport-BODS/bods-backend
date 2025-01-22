"""
Search a Zip of XMLs for a Tag
"""

import concurrent.futures
import os
from pathlib import Path

<<<<<<< HEAD
from structlog.stdlib import get_logger

from .common import process_zip_contents
from .csv_output import write_csv_reports
from .models import AnalysisMode, XMLTagInfo

log = get_logger()
=======
from .common import log, AnalysisMode
from .models import XMLTagInfo
from .report import write_csv_reports
from .xml_processor import process_zip_contents
>>>>>>> 7b7d62c (refactored to module)


def process_zip_file_parallel(
    zip_path: str, tag_name: str, sub_zip_workers: int = 4
) -> None:
    """Process a zip file and generate both detailed and summary reports"""
    if not os.path.exists(zip_path):
        log.error("Input file not found", zip_path=zip_path)
        raise FileNotFoundError(zip_path)

    log.info(
        "Processing ZIP File",
        zip_path=zip_path,
        tag_name=tag_name,
        sub_zip_workers=sub_zip_workers,
    )
    xml_files: list[XMLTagInfo] = list(  # type: ignore
        process_zip_contents(
            zip_path,
            max_workers=sub_zip_workers,
            mode=AnalysisMode.TAG,
            tag_name=tag_name,
        )
    )

    # Generate reports
    output_path = Path(zip_path).with_suffix(".csv")
    write_csv_reports(
        xml_files=xml_files,  # type: ignore
        base_path=output_path,
        mode=AnalysisMode.TAG,
        tag_name=tag_name,
    )


def analyze_tags(
    zip_files: list[Path],
    tag_name: str,
    sub_zip_workers: int = 4,
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
            except Exception:  # pylint: disable=broad-except
                log.error("Error processing zip file", exc_info=True)
