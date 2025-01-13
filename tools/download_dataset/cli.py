"""
Runs the File Attributes ETL Process against specified database
"""

import typer
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

from timetables_etl.download_dataset import (
    DownloadDatasetInputData,
    download_and_upload_dataset,
)
from tools.common.db_tools import create_db_config, setup_db_instance

app = typer.Typer()
log = get_logger()


@app.command()
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
    use_dotenv: bool = typer.Option(
        True,
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
        raise typer.Exit(1)
    db = setup_db_instance(db_config)
    event_data = DownloadDatasetInputData(
        **{
            "DatasetEtlTaskResultId": "1234",
            "Bucket": bucket,
            "ObjectKey": "dummy.xml",
            "URLLink": url_link,
            "DatasetRevisionId": revision_id,
        }
    )
    download_and_upload_dataset(
        db,
        event_data.s3_bucket_name,
        event_data.revision_id,
        event_data.remote_dataset_url_link,
        True,
    )


if __name__ == "__main__":
    app()
