"""
Serverless ETL task related data fetching from tables
"""

from pathlib import Path

from common_layer.database.models import DatasetETLTaskResult, FileProcessingResult
from common_layer.database.repos import ETLTaskResultRepo, FileProcessingResultRepo
from structlog.stdlib import get_logger

from .utils import SqlDB, csv_extractor

logger = get_logger()


@csv_extractor()
def extract_pipelines_datasetetltaskresult(
    db: SqlDB, revision_id: int
) -> list[DatasetETLTaskResult] | None:
    """
    Get the list of pipelines_datasetetltaskresult associated to a revision_id
    And output to csv
    """
    repo = ETLTaskResultRepo(db)
    return repo.get_by_revision_id(revision_id)


@csv_extractor()
def extract_pipelines_fileprocessingresult(
    db: SqlDB, revision_id: int
) -> list[FileProcessingResult]:
    """
    Get the list of pipelines_fileprocessingresult associated to a revision_id
    And output to csv
    """
    repo = FileProcessingResultRepo(db)
    return repo.get_by_revision_id(revision_id)


def process_etl_entities_by_revision_id(db: SqlDB, revision_id: int, output_path: Path):
    """
    Extract Data from DB tables related to ETL and Output to CSVs
    """
    logger.info("Starting etl related data extraction and output to CSV")
    extract_pipelines_datasetetltaskresult(db, revision_id, output_path=output_path)
    extract_pipelines_fileprocessingresult(db, revision_id, output_path=output_path)
    logger.info("Finished etl related data extraction/output to CSV")
