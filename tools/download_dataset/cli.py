"""
Runs the File Attributes ETL Process against specified database
"""

import typer
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

from src.timetables_etl.download_dataset.app.download_dataset import (
    download_and_upload_dataset,
)
from src.timetables_etl.download_dataset.app.models import DownloadDatasetInputData
from tools.common.db_tools import create_db_config, setup_db_instance

app = typer.Typer()
log = get_logger()


@app.command(name="download-dataset")
def main(
    db_host: str = typer.Option(
        "localhost",
        "--db-host",
        help="Database host",
    ),
    db_name: str = typer.Option(
        "bods-local",
        "--db-name",
        help="Database name",
    ),
    db_user: str = typer.Option(
        "bods-local",
        "--db-user",
        help="Database user",
    ),
    db_password: str = typer.Option(
        "bods-local",
        "--db-password",
        help="Database password",
    ),
    db_port: int = typer.Option(
        5432,
        "--db-port",
        help="Database port",
    ),
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
    bucket: str = typer.Option(
        "bodds-dev",
        "--bucket",
        help="S3 bucket name",
    ),
    url_link: str = typer.Option(
        "https://s3.eu-west-2.amazonaws.com/bodds-test.ops.itoworld.com/Automation_Testing/Timetables/PTI_PASS_DQ_PASS_t9cTb8A%2BTimetable.xml",
        "--url-link",
        help="Remote file url link",
    ),
    etl_task_result_id: int = typer.Option(
        5432,
        "--etl-task-result-id",
        help="Dataset ETL Task Result ID",
    ),
    use_dotenv: bool = typer.Option(
        False,
        "--use-dotenv",
        help="Load database configuration from .env file",
    ),
):
    """Process TXC XML files for transformation testing"""
    if log_json:
        configure_logging()
    try:
        db_config = create_db_config(
            use_dotenv, db_host, db_port, db_name, db_user, db_password
        )
    except ValueError as e:
        log.error("Database configuration error", exc_info=True)
        raise typer.Exit(1) from e
    db = setup_db_instance(db_config)
    event_data = DownloadDatasetInputData(
        DatasetEtlTaskResultId=etl_task_result_id,
        Bucket=bucket,
        Url=url_link,  # type: ignore
        DatasetRevisionId=revision_id,
    )
    download_and_upload_dataset(db, event_data)


if __name__ == "__main__":
    app()
