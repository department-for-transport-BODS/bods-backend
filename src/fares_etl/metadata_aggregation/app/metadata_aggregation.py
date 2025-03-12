"""
Aggregates metadata from dynamodb and stores it in primary database
"""

from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database.client import SqlDB
from common_layer.dynamodb.client.fares_metadata import DynamoDBFaresMetadata
from pydantic import BaseModel, Field
from structlog import get_logger

from .load.dataset import load_dataset
from .load.metadata import load_metadata
from .transform.transform_metadata import (
    aggregate_metadata,
    get_min_schema_version,
    map_metadata,
)

log = get_logger()


class MetadataAggregationInputData(BaseModel):
    """
    Input data for the Metadata Aggregation Function
    """

    task_id: int = Field(alias="DatasetEtlTaskResultId")
    revision_id: int = Field(alias="DatasetRevisionId")


def lambda_handler(event: dict[str, Any], _context: LambdaContext):
    """
    Fares Metadata Aggregation
    """
    log.debug("Input Data", data=event)
    input_data = MetadataAggregationInputData(**event)
    db = SqlDB()

    dynamodb_fares_metadata_repo = DynamoDBFaresMetadata()

    dynamo_db_data = dynamodb_fares_metadata_repo.get_all_data_for_task(
        input_data.task_id
    )

    dynamo_db_metadata = [
        item for item in dynamo_db_data if item["SK"].startswith("METADATA")
    ]

    fares_metadata, data_catalogues, stops, schema_versions = map_metadata(
        dynamo_db_metadata
    )

    min_schema_version = get_min_schema_version(schema_versions)
    aggregated_fares_metadata = aggregate_metadata(fares_metadata)

    metadata_dataset_id = load_dataset(input_data.revision_id, min_schema_version, db)

    aggregated_fares_metadata.datasetmetadata_ptr_id = metadata_dataset_id

    for data_catalogue in data_catalogues:
        data_catalogue.fares_metadata_id = metadata_dataset_id

    for stop in stops:
        stop.faresmetadata_id = metadata_dataset_id

    load_metadata(aggregated_fares_metadata, stops, data_catalogues, db)

    return {"status_code": 200, "message": "Fares Metadata Aggregation Completed"}
