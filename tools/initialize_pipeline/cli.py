"""
Runs PTI Validation against specified database
"""

import typer
from common_layer.dynamodb.client import DynamoDB
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

from src.timetables_etl.initialize_pipeline.app.initialize_pipeline import (
    InitializePipelineEvent,
    initialize_pipeline,
)
from tools.common.db_tools import create_db_config, dotenv_loader, setup_db_instance

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
    dynamodb = DynamoDB()

    event = InitializePipelineEvent(DatasetRevisionId=revision_id)

    initialize_pipeline(db, dynamodb, event)


if __name__ == "__main__":
    app()
