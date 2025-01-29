"""
Database View Tool to search by revision id or service ID
"""

from pathlib import Path

import typer
from common_layer.database.client import SqlDB
from common_layer.database.models import NaptanStopPoint
from common_layer.database.models.model_transmodel import (
    TransmodelServicePattern,
    TransmodelServicePatternStop,
)
from common_layer.database.repos import NaptanStopPointRepo
from structlog.stdlib import get_logger
from typer import BadParameter, Option, Typer

from tools.common.db_tools import DbConfig, create_db_config, setup_db_instance

from .etl_task import process_etl_entities_by_revision_id
from .organisation import (
    extract_dataset,
    extract_dataset_revision,
    extract_organisation,
    extract_txc_attributes,
)
from .transmodel import (
    extract_bookingarrangements,
    extract_flexibleserviceoperationperiod,
    extract_service_by_id,
    extract_service_service_patterns,
    extract_servicedorganisations,
    extract_servicedorganisationvehiclejourney,
    extract_servicedorganisationworkingdays,
    extract_servicepattern_localities,
    extract_servicepatterns_by_ids,
    extract_servicepatterns_by_revision_id,
    extract_servicepatternstop,
    extract_services_by_revision_id,
    extract_stopactivity,
    extract_vehiclejourney,
)
from .utils import csv_extractor

logger = get_logger()
app = Typer()


@csv_extractor()
def extract_stoppoint(db: SqlDB, atco_codes: list[str]) -> list[NaptanStopPoint]:
    """
    Extract naptan stoppoint details from DB.
    """
    repo = NaptanStopPointRepo(db)
    stop_points, missing_stops = repo.get_by_atco_codes(atco_codes)
    if missing_stops:
        logger.warning("Some Stops were not found in DB", missing_stops=missing_stops)
    return stop_points


def process_vehicle_journeys(
    db: SqlDB,
    service_pattern_stops: list[TransmodelServicePatternStop],
    output_path: Path,
):
    """
    Process Vehicle Journeys
    """
    vehicle_journey_ids = [
        result.vehicle_journey_id for result in service_pattern_stops
    ]
    extract_vehiclejourney(db, vehicle_journey_ids, output_path=output_path)
    extract_flexibleserviceoperationperiod(
        db, vehicle_journey_ids, output_path=output_path
    )
    serviced_org_vj = extract_servicedorganisationvehiclejourney(
        db, vehicle_journey_ids, output_path=output_path
    )
    extract_servicedorganisations(
        db,
        [it.serviced_organisation_id for it in serviced_org_vj],
        output_path=output_path,
    )
    extract_servicedorganisationworkingdays(
        db,
        [it.id for it in serviced_org_vj],
        output_path=output_path,
    )


def process_service_patterns(
    db: SqlDB,
    tm_service_patterns: list[TransmodelServicePattern],
    output_path: Path,
):
    """
    Items dependent on service patterns
    """
    service_pattern_ids = [result.id for result in tm_service_patterns]
    service_pattern_stops = extract_servicepatternstop(
        db, service_pattern_ids, output_path=output_path
    )
    extract_servicepattern_localities(db, service_pattern_ids, output_path=output_path)
    extract_stoppoint(
        db,
        [result.atco_code for result in service_pattern_stops],
        output_path=output_path,
    )
    stop_activity_ids = [result.stop_activity_id for result in service_pattern_stops]

    extract_stopactivity(db, stop_activity_ids, output_path=output_path)
    process_vehicle_journeys(db, service_pattern_stops, output_path)


def process_from_service_id(
    db: SqlDB,
    service_id: int,
    output_path: Path,
):
    """
    Process data from Service ID
    """
    log = logger.bind(operation="batch_extraction")
    service = extract_service_by_id(db, service_id, output_path=output_path)
    if service is None:
        log.error("Transmodel Service Not Found")
        raise BadParameter("Transmodel Service was not found in Database")
    extract_bookingarrangements(db, [service.id], output_path=output_path)
    service_service_patterns = extract_service_service_patterns(
        db, [service.id], output_path=output_path
    )
    service_pattern_ids = [sp.servicepattern_id for sp in service_service_patterns]
    service_patterns = extract_servicepatterns_by_ids(db, service_pattern_ids)
    process_service_patterns(db, service_patterns, output_path=output_path)


def process_from_revision_id(
    db: SqlDB,
    revision_id: int,
    output_path: Path,
):
    """
    Extract Data from DB and Output to CSVs based on table name
    """
    log = logger.bind(operation="batch_extraction")
    log.info("Starting DB Data extraction and output to CSV")

    # Organisation related entity
    dataset_revision = extract_dataset_revision(
        db, revision_id, output_path=output_path
    )
    dataset = extract_dataset(db, dataset_revision.dataset_id, output_path=output_path)
    if dataset:
        extract_organisation(db, dataset.organisation_id, output_path=output_path)
    extract_txc_attributes(db, revision_id, output_path=output_path)

    # Transmodel related entities
    tm_services = extract_services_by_revision_id(
        db, revision_id, output_path=output_path
    )
    service_ids = [it.id for it in tm_services]

    extract_service_service_patterns(db, service_ids, output_path=output_path)

    extract_bookingarrangements(db, service_ids, output_path=output_path)
    service_patterns = extract_servicepatterns_by_revision_id(
        db, revision_id, output_path=output_path
    )
    process_service_patterns(db, service_patterns, output_path)


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
    db_config: DbConfig, revision_id: int | None, service_id: int | None
) -> Path:
    """
    Generate a default output path based on revision_id or service_id.
    Creates directories if they don't exist.

    Base path is ./data/db_viewer/ with either revision_id/<id> or service_id/<id>
    """
    base_path = Path("./data/db_viewer")

    if not base_path.exists():
        logger.info("Creating base directory structure", path=str(base_path))
        base_path.mkdir(parents=True, exist_ok=True)

    db_host_port = f"{db_config.host}-{db_config.port}"

    if revision_id is not None:
        final_path = base_path / db_host_port / "revision_id" / str(revision_id)
    else:
        final_path = base_path / db_host_port / "service_id" / str(service_id)

    if not final_path.exists():
        logger.info("Creating output directory", path=str(final_path))
        final_path.mkdir(parents=True, exist_ok=True)

    return final_path


@app.command()
def main(
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
):
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
        logger.error("Database configuration error", error=str(e))
        raise typer.Exit(1)
    db = setup_db_instance(config)
    if output_path is None:
        output_path = make_default_output_path(config, revision_id, service_id)
    if revision_id:
        process_from_revision_id(
            db=db, revision_id=revision_id, output_path=output_path
        )
    if service_id:
        process_from_service_id(db, service_id, output_path)

    if etl_result and revision_id:
        process_etl_entities_by_revision_id(db, revision_id, output_path=output_path)

    logger.info("Completed Processing", output_path=output_path)


if __name__ == "__main__":
    app()
