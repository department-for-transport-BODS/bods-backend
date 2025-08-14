"""
Aggregates metadata from dynamodb and stores it in primary database
"""

from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database.client import SqlDB
from common_layer.database.models import (
    FaresDataCatalogueMetadata,
    FaresMetadata,
    FaresMetadataStop,
    FaresValidation,
)
from common_layer.database.repos import (
    DataQualitySchemaViolationRepo,
    OrganisationDatasetRepo,
    OrganisationDatasetRevisionRepo,
)
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.dynamodb.client.fares_metadata import DynamoDBFaresMetadata
from common_layer.exceptions import FaresMetadataNotFound, SchemaViolationsFound
from common_layer.utils import send_failure_email
from pydantic import BaseModel, Field
from structlog.stdlib import get_logger

from .load.dataset import load_dataset
from .load.metadata import load_metadata
from .load.violations import load_violations
from .transform.transform_metadata import (
    aggregate_metadata,
    get_min_schema_version,
    map_metadata,
)
from .transform.transform_violations import map_violations

log = get_logger()


class MetadataAggregationInputData(BaseModel):
    """
    Input data for the Metadata Aggregation Function
    """

    task_id: int = Field(alias="DatasetEtlTaskResultId")
    revision_id: int = Field(alias="DatasetRevisionId")


def get_organisation_id_from_revision_id(db: SqlDB, revision_id: int) -> int:
    """
    Retrieve the organisation ID associated with a given revision ID.
    """

    org_dataset_revision = OrganisationDatasetRevisionRepo(db).require_by_id(
        revision_id
    )
    organisation_dataset = OrganisationDatasetRepo(db).require_by_id(
        org_dataset_revision.dataset_id
    )

    return organisation_dataset.organisation_id


def get_data_from_dynamodb(
    task_id: int, revision_id: int, db: SqlDB
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Get data from dynamodb
    """
    dynamodb_fares_metadata_repo = DynamoDBFaresMetadata()

    dynamodb_data = dynamodb_fares_metadata_repo.get_all_data_for_task(task_id)

    dynamodb_metadata = [
        item for item in dynamodb_data if item["SK"]["S"].startswith("METADATA#")
    ]

    dynamodb_violations = [
        item for item in dynamodb_data if item["SK"]["S"].startswith("VIOLATION#")
    ]

    if len(dynamodb_metadata) == 0:
        schema_violations = DataQualitySchemaViolationRepo(db).get_by_revision_id(
            revision_id
        )

        if schema_violations and len(schema_violations) > 0:
            log.info(
                "Sending Fares validation email for revision", revision_id=revision_id
            )
            send_failure_email(db, revision_id)
            raise SchemaViolationsFound(task_id=task_id)

        log.error("No Fares metadata found in dynamodb for task", task_id=task_id)
        raise FaresMetadataNotFound(task_id=task_id)

    return dynamodb_metadata, dynamodb_violations


def load_dataset_to_database(
    db: SqlDB, revision_id: int, schema_versions: list[str]
) -> int:
    """
    Write fares dataset to database
    """
    min_schema_version = get_min_schema_version(schema_versions)

    metadata_dataset_id = load_dataset(db, revision_id, min_schema_version)

    return metadata_dataset_id


def load_metadata_to_database(
    db: SqlDB,
    metadata: list[FaresMetadata],
    stops: list[FaresMetadataStop],
    data_catalogues: list[FaresDataCatalogueMetadata],
    metadata_dataset_id: int,
) -> None:
    """
    Write metadata to database
    """

    aggregated_fares_metadata = aggregate_metadata(metadata, data_catalogues)
    aggregated_fares_metadata.datasetmetadata_ptr_id = metadata_dataset_id

    for data_catalogue in data_catalogues:
        data_catalogue.fares_metadata_id = metadata_dataset_id

    for stop in stops:
        stop.faresmetadata_id = metadata_dataset_id

    load_metadata(db, aggregated_fares_metadata, stops, data_catalogues)


def verify_and_send_error_email(
    db: SqlDB, revision_id: int, violations: list[FaresValidation]
):
    """Send email based of fares validation error or schema error

    Args:
        db (SqlDB): DB instance for query
        revision_id (int): revision id for dataset
        violations (list[FaresValidation]): violations for fares dataset
    """
    schema_violations = DataQualitySchemaViolationRepo(db).get_by_revision_id(
        revision_id
    )

    if (schema_violations and len(schema_violations) > 0) or (
        violations and len(violations) > 0
    ):
        log.info("Sending Fares validation email for revision", revision_id=revision_id)
        send_failure_email(db, revision_id)


@file_processing_result_to_db(step_name=StepName.FARES_METADATA_AGGREGATION)
def lambda_handler(
    event: dict[str, Any], _context: LambdaContext
) -> dict[str, int | str]:
    """
    Fares Metadata Aggregation
    """

    log.debug("Input Data", data=event)
    input_data = MetadataAggregationInputData(**event)

    db = SqlDB()

    organisation_id = get_organisation_id_from_revision_id(db, input_data.revision_id)

    dynamodb_metadata, dynamodb_violations = get_data_from_dynamodb(
        input_data.task_id,
        input_data.revision_id,
        db,
    )

    fares_metadata, data_catalogues, stops, schema_versions = map_metadata(
        dynamodb_metadata
    )

    violations, fares_validation_result = map_violations(
        dynamodb_violations, organisation_id, input_data.revision_id
    )

    metadata_dataset_id = load_dataset_to_database(
        db, input_data.revision_id, schema_versions
    )

    load_metadata_to_database(
        db,
        fares_metadata,
        stops,
        data_catalogues,
        metadata_dataset_id,
    )

    verify_and_send_error_email(db, input_data.revision_id, violations)

    load_violations(db, violations, fares_validation_result)

    return {
        "status_code": 200,
        "message": "Fares Metadata Aggregation Completed",
        "fares_metadata_count": len(fares_metadata),
        "stops_count": len(stops),
        "data_catalogues_count": len(data_catalogues),
        "violations_count": len(violations),
    }
