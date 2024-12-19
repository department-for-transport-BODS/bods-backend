"""
Processing functions
"""

import asyncio
import multiprocessing as mp
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from common_layer.database.create_tables import create_db_tables
from common_layer.txc.parser.parser_txc import parse_txc_file
from structlog.stdlib import get_logger

from timetables_etl.etl.app.pipeline import transform_data
from tools.common.db_tools import setup_process_db
from tools.common.models import TestConfig
from tools.local_etl.mock_task_data import create_task_data
from tools.local_etl.timing import TimingStats, print_timing_report

log = get_logger()


def process_single_file(config: TestConfig, file_path: Path) -> TimingStats:
    """Process a single XML file and return timing statistics"""
    # Create a new database connection for each process
    db = setup_process_db(config)

    stats = TimingStats(file_path=file_path)
    start_time = time.time()

    try:
        # Time parsing
        parse_start = time.time()
        txc = parse_txc_file(file_path, parse_track_data=True, parse_file_hash=True)
        stats.parse_time = time.time() - parse_start

        # Time transformation
        transform_start = time.time()
        task_data = create_task_data(txc)

        log.info("✅ Setup Complete, starting ETL Task")
        transform_data(txc, task_data, db)
        stats.transform_time = time.time() - transform_start

    except Exception as e:  # pylint: disable=broad-exception-caught
        stats.status = "error"
        stats.error = str(e)
        log.error("Error processing file", file=file_path, exception=str(e))

    stats.total_time = time.time() - start_time
    return stats


def process_files_sequential(
    files: list[Path], config: TestConfig
) -> list[TimingStats]:
    """Process multiple files sequentially"""
    timing_stats = []
    setup_process_db(config)

    log.info("Starting sequential processing", total_files=len(files))

    for file_path in files:
        stats = process_single_file(config, file_path)
        timing_stats.append(stats)
        log.info(
            "File processed",
            file=file_path.name,
            status=stats.status,
            time_taken=round(stats.total_time, 2),
        )

    return timing_stats


async def process_files_parallel(
    files: list[Path], config: TestConfig
) -> list[TimingStats]:
    """Process multiple files in parallel using ProcessPoolExecutor"""
    timing_stats = []
    max_workers = config.max_workers or mp.cpu_count()
    chunk_size = max(1, len(files) // (max_workers * 4))

    log.info(
        "Starting parallel processing",
        max_workers=max_workers,
        total_files=len(files),
        chunk_size=chunk_size,
    )

    loop = asyncio.get_event_loop()

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Create tasks for all files
        futures = [
            loop.run_in_executor(executor, process_single_file, config, file_path)
            for file_path in files
        ]

        # Process files as they complete
        for completed_task in asyncio.as_completed(futures):
            try:
                stats = await completed_task
                timing_stats.append(stats)
                log.info(
                    "File processed",
                    file=stats.file_path.name,
                    status=stats.status,
                    time_taken=round(stats.total_time, 2),
                )
            except Exception as e:  # pylint: disable=broad-exception-caught
                log.error("Unexpected error in parallel processing", error=str(e))

    return timing_stats


async def process_files(config: TestConfig):
    """Process files based on configuration"""
    start_time = time.time()
    create_db_tables(setup_process_db(config))

    log.info(
        "Starting processing",
        mode="parallel" if config.parallel else "sequential",
        file_count=len(config.txc_paths),
    )

    timing_stats = (
        await process_files_parallel(config.txc_paths, config)
        if config.parallel
        else process_files_sequential(config.txc_paths, config)
    )

    total_time = time.time() - start_time
    print_timing_report(timing_stats, total_time)
