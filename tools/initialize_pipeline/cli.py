"""
Runs PTI Validation against specified database
"""

from io import BytesIO
from pathlib import Path

import typer
from common_layer import dynamodb
from common_layer.dynamodb.client import DynamoDB, DynamoDBSettings
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

from timetables_etl.initialize_pipeline import (
    InitializePipelineEvent,
    initialize_pipeline,
)
from tools.common.db_tools import create_db_config, setup_db_instance

app = typer.Typer()
log = get_logger()


@app.command(name="initialize-pipeline")
def main(
    revision_id: int = typer.Option(
        5432,
        "--revision-id",
        help="The Revision ID to use",
    ),
    log_json: bool = typer.Option(
        False,
        "--log-json",
        help="Enable Structured logging output",
    ),
):
    """Run PTI Validation on given TXC XML files for testing"""
    if log_json:
        configure_logging()
    try:
        db_config = create_db_config(use_dotenv=True)
    except ValueError as e:
        log.error("Database configuration error", exc_info=True)
        raise typer.Exit(1)

    db = setup_db_instance(db_config)
    dynamodb = DynamoDB(
        DynamoDBSettings(
            DYNAMODB_ENDPOINT_URL="http://localhost:4566",
            DYNAMODB_TABLE_NAME="bods-backend-local-tt-cache",
        )
    )

    event = InitializePipelineEvent(DatasetRevisionId=revision_id)

    initialize_pipeline(db, dynamodb, event)


if __name__ == "__main__":
    app()
