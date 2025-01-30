"""
Data Quality Data fetching
"""

from pathlib import Path

from common_layer.database.models import (
    DataQualityPostSchemaViolation,
    DataQualityPTIObservation,
    DataQualitySchemaViolation,
)
from common_layer.database.repos import (
    DataQualityPostSchemaViolationRepo,
    DataQualityPTIObservationRepo,
    DataQualitySchemaViolationRepo,
)
from structlog.stdlib import get_logger

from .utils import SqlDB, csv_extractor

logger = get_logger()


@csv_extractor()
def extract_data_quality_postschemaviolation(
    db: SqlDB, revision_id: int
) -> list[DataQualityPostSchemaViolation] | None:
    """
    Get the list of data_quality_postschemaviolation associated to a
    revision_id and output to csv
    """
    repo = DataQualityPostSchemaViolationRepo(db)
    return repo.get_by_revision_id(revision_id)


@csv_extractor()
def extract_data_quality_schemaviolation(
    db: SqlDB, revision_id: int
) -> list[DataQualitySchemaViolation] | None:
    """
    Get the list of data_quality_schemaviolation associated to a
    revision_id and output to csv
    """
    repo = DataQualitySchemaViolationRepo(db)
    return repo.get_by_revision_id(revision_id)


@csv_extractor()
def extarct_data_quality_ptiobservation(
    db: SqlDB, revision_id: int
) -> list[DataQualityPTIObservation] | None:
    """
    Get the list of data_quality_ptiobservation associated to a
    revision_id and output to csv
    """
    repo = DataQualityPTIObservationRepo(db)
    return repo.get_by_revision_id(revision_id)


def process_data_quality_entities_by_revision_id(
    db: SqlDB, revision_id: int, output_path: Path
):
    """
    Extract Data from DB tables related to ETL and Output to CSVs
    """
    logger.info("Starting data quality data extraction and output to CSV")
    extract_data_quality_postschemaviolation(db, revision_id, output_path=output_path)
    extract_data_quality_schemaviolation(db, revision_id, output_path=output_path)
    extarct_data_quality_ptiobservation(db, revision_id, output_path=output_path)
    logger.info("Finished data quality data extraction and output to CSV")
