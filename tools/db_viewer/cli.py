"""
Database View Tool to search by revision id or service ID
"""

from enum import Enum
from pathlib import Path

import typer
from structlog.stdlib import get_logger
from typer import BadParameter, Option, Typer

from tools.common.db_tools import DbConfig, create_db_config, setup_db_instance

from .data_quality import process_data_quality_entities_by_revision_id
from .etl_task import process_etl_entities_by_revision_id
from .fares import fares_from_revision_id
from .timetables import process_from_revision_id, process_from_service_id

log = get_logger()
app = Typer()


class DatasetType(str, Enum):
    """
    Dataset type to fetch
    """

    TIMETABLES = "timetables"
    FARES = "fares"


def validate_params(revision_id: int | None, service_id: int | None) -> None:
    """
    Validate command line parameter
    """
    if revision_id and service_id:
        raise BadParameter(
            "Only one of 'revision_id' or 'service_id' should be provided."
        )
    if revision_id is None and service_id is None:
        raise BadParameter(
            "At least one of 'revision_id' or 'service_id' must be provided."
        )


def make_default_output_path(
    db_config: DbConfig,
    dataset_type: DatasetType,
    revision_id: int | None,
    service_id: int | None,
) -> Path:
    """
    Generate a default output path based on revision_id or service_id.
    Creates directories if they don't exist.

    Base path is ./data/db_viewer/ with either revision_id/<id> or service_id/<id>
    """
    base_path = Path("./data/db_viewer")

    if not base_path.exists():
        log.info("Creating base directory structure", path=str(base_path))
        base_path.mkdir(parents=True, exist_ok=True)

    db_host_port = f"{db_config.host}-{db_config.port}"

    if revision_id is not None:
        final_path = (
            base_path
            / db_host_port
            / dataset_type.value
            / "revision_id"
            / str(revision_id)
        )
    else:
        final_path = (
            base_path
            / db_host_port
            / dataset_type.value
            / "service_id"
            / str(service_id)
        )

    if not final_path.exists():
        log.info("Creating output directory", path=str(final_path))
        final_path.mkdir(parents=True, exist_ok=True)

    return final_path


@app.command()
def main(  # pylint: disable=too-many-arguments, too-many-positional-arguments
    output_path: Path | None = Option(
        None,
        "--output-path",
        help="Paths to csv files",
    ),
    db_host: str = Option(
        "localhost",
        "--db-host",
        help="Database host",
    ),
    db_name: str = Option(
        "bods-local",
        "--db-name",
        help="Database name",
    ),
    db_user: str = Option(
        "bods-local",
        "--db-user",
        help="Database user",
    ),
    db_password: str = Option(
        "bods-local",
        "--db-password",
        help="Database password",
    ),
    db_port: int = Option(
        5432,
        "--db-port",
        help="Database port",
    ),
    revision_id: int | None = Option(
        None,
        "--revision-id",
        help="Dataset revision id",
    ),
    service_id: int | None = Option(
        None,
        "--service-id",
        help="Service id",
    ),
    etl_result: bool = Option(
        False,
        "--etl-result",
        help="Extract the data from ETL pipelines tables",
    ),
    use_dotenv: bool = Option(
        False,
        "--use-dotenv",
        help="Load database configuration from .env file",
    ),
    dataset_type: DatasetType = Option(
        DatasetType.TIMETABLES, "--type", help="Which type of dataset to fetch"
    ),
) -> None:
    """
    This tool queries a database then creates CSVs for ETL data for a
    specific revision id or service id
    """
    validate_params(revision_id, service_id)
    try:
        config = create_db_config(
            use_dotenv, db_host, db_port, db_name, db_user, db_password
        )
    except ValueError as e:
        log.error("Database configuration error", error=str(e))
        raise typer.Exit(1)
    db = setup_db_instance(config)
    if output_path is None:
        output_path = make_default_output_path(
            config, dataset_type, revision_id, service_id
        )

    match dataset_type:
        case DatasetType.TIMETABLES:

            if revision_id:
                process_from_revision_id(
                    db=db, revision_id=revision_id, output_path=output_path
                )
            if service_id:
                process_from_service_id(db, service_id, output_path)

            if etl_result and revision_id:
                process_etl_entities_by_revision_id(
                    db, revision_id, output_path=output_path
                )
                process_data_quality_entities_by_revision_id(
                    db, revision_id, output_path=output_path
                )
        case DatasetType.FARES:
            log.info("Processing Fares")
            if revision_id:
                fares_from_revision_id(db, revision_id, output_path)
            else:
                log.critical("Fares Extraction Requires revision id")
    log.info("Completed Processing", output_path=str(output_path))


if __name__ == "__main__":
    app()
