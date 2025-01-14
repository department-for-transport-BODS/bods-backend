"""
Runs PTI Validation against specified database
"""

from io import BytesIO
from pathlib import Path

import typer
from common_layer.dynamodb.client import DynamoDB, DynamoDBSettings
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

from timetables_etl.pti_validation import (
    PTIValidationEvent,
    get_task_data,
    run_validation,
)
from tools.common.db_tools import create_db_config, setup_db_instance

app = typer.Typer()
log = get_logger()


@app.command(name="pti-validation")
def main(
    revision_id: int = typer.Option(
        5432,
        "--revision-id",
        help="The Revision ID to use",
    ),
    xml_file_name: str = typer.Option(
        "",
        "--filename",
        help="Local filename",
    ),
    file_attributes_id: int = typer.Option(
        None,
        "--file-attributes-id",
        help="TXC File attributes ID",
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

    with open(xml_file_name, "rb") as xml_file:
        event = PTIValidationEvent(
            DatasetRevisionId=revision_id,
            Bucket="bucket-name",
            ObjectKey="object-key",
            TxcFileAttributesId=file_attributes_id,
        )
        file = BytesIO(xml_file.read())

        task_data = get_task_data(event, file, db, dynamodb)
        run_validation(task_data, db, dynamodb)


if __name__ == "__main__":
    app()
