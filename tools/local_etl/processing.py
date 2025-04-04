"""
Processing functions
"""

import asyncio
import multiprocessing as mp
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from common_layer.database.client import ProjectEnvironment
from common_layer.database.create_tables import create_db_tables
from common_layer.dynamodb.client import DynamoDbCacheSettings
from common_layer.dynamodb.client.cache import DynamoDBCache
from common_layer.dynamodb.client.naptan_stop_points import (
    NaptanDynamoDBSettings,
    NaptanStopPointDynamoDBClient,
)
from common_layer.dynamodb.data_manager import FileProcessingDataManager
from common_layer.xml.txc.parser.parser_txc import parse_txc_file
from structlog.stdlib import get_logger

from timetables_etl.etl.app.etl_process import PARSER_CONFIG
from timetables_etl.etl.app.models import ETLTaskClients
from timetables_etl.etl.app.pipeline import transform_data
from tools.common.db_tools import setup_db_instance
from tools.common.models import TestConfig
from tools.local_etl.make_task_data import create_task_data_from_inputs
from tools.local_etl.timing import TimingStats, print_timing_report

log = get_logger()


def process_single_file(config: TestConfig, file_path: Path) -> TimingStats:
    """Process a single XML file and return timing statistics"""
    # Create a new database connection for each process
    db = setup_db_instance(config.db_config)

    # Create stop_point_client with env set to dev (will use AWS profile instead of localstack)
    stop_point_client = NaptanStopPointDynamoDBClient(
        NaptanDynamoDBSettings(
            PROJECT_ENV=ProjectEnvironment.DEVELOPMENT,
            DYNAMODB_NAPTAN_STOP_POINT_TABLE_NAME="bods-backend-dev-naptan-stop-points-table",
            DYNAMODB_ENDPOINT_URL="",
        )
    )
    dynamodb = DynamoDBCache(
        DynamoDbCacheSettings(
            PROJECT_ENV=ProjectEnvironment.DEVELOPMENT,
            DYNAMODB_CACHE_TABLE_NAME="bods-backend-dev-tt-cache",
        )
    )
    dynamo_data_manager = FileProcessingDataManager(db, dynamodb)
    stats = TimingStats(file_path=file_path)
    start_time = time.time()

    try:
        # Time parsing
        parse_start = time.time()
        txc = parse_txc_file(file_path, PARSER_CONFIG)
        stats.parse_time = time.time() - parse_start

        # Time transformation
        transform_start = time.time()
        task_data = create_task_data_from_inputs(
            txc, config.task_id, config.file_attributes_id, config.revision_id, db
        )
        task_clients = ETLTaskClients(
            db=db,
            stop_point_client=stop_point_client,
            dynamo_data_manager=dynamo_data_manager,
        )
        log.info("✅ Setup Complete, starting ETL Task")
        transform_data(txc, task_data, task_clients)
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
    timing_stats: list[TimingStats] = []
    setup_db_instance(config.db_config)

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
    timing_stats: list[TimingStats] = []
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
    if config.create_tables:
        log.warning(
            "Creating Database Tables (And potentially modifying existing ones!)"
        )
        create_db_tables(setup_db_instance(config.db_config))

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
