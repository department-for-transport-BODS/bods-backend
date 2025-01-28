"""
Runs PTI Validation against specified database
"""

from io import BytesIO

import typer
from common_layer.dynamodb.client import DynamoDB
from common_layer.dynamodb.client.cache import DynamoDBCache
from common_layer.dynamodb.client.naptan_stop_points import (
    NaptanStopPointDynamoDBClient,
)
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

from src.timetables_etl.pti.app.pti_validation import (
    PTIValidationEvent,
    get_task_data,
    run_validation,
)
from tools.common.db_tools import create_db_config, dotenv_loader, setup_db_instance

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
    use_dotenv: bool = typer.Option(
        False,
        "--use-dotenv",
        help="Load database and dynamodb configurations from .env file",
    ),
):
    """Run PTI Validation on given TXC XML files for testing"""
    if log_json:
        configure_logging()

    if use_dotenv:
        dotenv_loader()

    try:
        db_config = create_db_config(use_dotenv=use_dotenv)
    except ValueError as e:
        log.error("Database configuration error", exc_info=True)
        raise typer.Exit(1) from e

    db = setup_db_instance(db_config)
    dynamodb = DynamoDBCache()
    stop_point_client = NaptanStopPointDynamoDBClient()

    with open(xml_file_name, "rb") as xml_file:
        event = PTIValidationEvent(
            DatasetRevisionId=revision_id,
            Bucket="bucket-name",
            ObjectKey="object-key",
            TxcFileAttributesId=file_attributes_id,
        )
        file = BytesIO(xml_file.read())

        task_data = get_task_data(event, file, db, dynamodb)
        run_validation(task_data, db, dynamodb, stop_point_client)


if __name__ == "__main__":
    app()
