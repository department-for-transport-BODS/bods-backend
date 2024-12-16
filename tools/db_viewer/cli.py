from pathlib import Path
from typer import Typer, Option, BadParameter
from structlog.stdlib import get_logger
from common_layer.database.models import NaptanStopPoint
from common_layer.database.repos import NaptanStopPointRepo
from .config import DbConfig
from .organisation import (
    extract_dataset_revision,
    extract_dataset,
    extract_organisation,
    extract_txc_attributes,
)
from .transmodel import (
    extract_service_by_revision_id,
    extract_service_by_id,
    extract_servicepattern,
    extract_servicepatternstop,
    extract_stopactivity,
    extract_service_service_patterns,
    extract_servicepattern_localities,
    extract_vehiclejourney,
    extract_bookingarrangements,
    extract_flexibleserviceoperationperiod,
    extract_servicedorganisationvehiclejourney,
    extract_servicedorganisations,
    extract_servicedorganisationworkingdays,
)
from .utils import (
    get_db_instance,
    SqlDB,
    csv_extractor,
)

logger = get_logger()
app = Typer()


@csv_extractor()
def extarct_stoppoint(db: SqlDB, locality_ids: list[int]) -> list[NaptanStopPoint]:
    """
    Extract naptan stoppoint details from DB.
    """
    repo = NaptanStopPointRepo(db)
    return repo.get_by_locality_ids(locality_ids)


def process_data_extraction(
    db: SqlDB,
    revision_id: int,
    service_id: int | None = None,
    output_path: Path | str | None = None,
):
    log = logger.bind(operation="batch_extraction")
    log.info("Starting DB Data extraction and output to CSV")

    if service_id:
        result = extract_service_by_id(service_id)
        revision_id = result.id

    # Organisation related entity
    result = extract_dataset_revision(db, revision_id, output_path=output_path)
    dataset_id = result.dataset_id
    result = extract_dataset(db, dataset_id, output_path=output_path)
    organisation_id = result.organisation_id
    extract_organisation(db, organisation_id, output_path=output_path)
    extract_txc_attributes(db, revision_id, output_path=output_path)

    # Transmodel related entities
    results = extract_service_by_revision_id(db, revision_id, output_path=output_path)
    service_ids = list(set([result.id for result in results]))

    results = extract_servicepattern(db, revision_id, output_path=output_path)
    service_pattern_ids = list(set([result.id for result in results]))

    results = extract_servicepatternstop(
        db, service_pattern_ids, output_path=output_path
    )
    stop_activity_ids = list(set([result.stop_activity_id for result in results]))
    vehicle_journey_ids = list(set([result.vehicle_journey_id for result in results]))
    extract_vehiclejourney(db, vehicle_journey_ids, output_path=output_path)

    results = extract_servicepattern_localities(db, service_pattern_ids, output_path=output_path)

    extarct_stoppoint(
        db,
        list(set([result.locality_id for result in results])),
        output_path=output_path,
    )

    extract_stopactivity(db, stop_activity_ids, output_path=output_path)

    extract_service_service_patterns(db, service_ids, output_path=output_path)

    extract_bookingarrangements(db, service_ids, output_path=output_path)
    extract_flexibleserviceoperationperiod(
        db, vehicle_journey_ids, output_path=output_path
    )
    results = extract_servicedorganisationvehiclejourney(
        db, vehicle_journey_ids, output_path=output_path
    )

    extract_servicedorganisations(
        db,
        list(set([it.serviced_organisation_id for it in results])),
        output_path=output_path,
    )
    extract_servicedorganisationworkingdays(
        db,
        list(set([it.id for it in results])),
        output_path=output_path,
    )


def validate_params(revision_id: int, service_id: int) -> None:
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


@app.command()
def main(
    location: Path = Option(
        None,
        "--dir",
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
    revision_id: int = Option(
        None,
        "--revision-id",
        help="Dataset revision id",
    ),
    service_id: int = Option(
        None,
        "--service-id",
        help="Service id",
    ),
):
    config = DbConfig(
        host=db_host, port=db_port, user=db_user, password=db_password, database=db_name
    )
    db = get_db_instance(config)
    process_data_extraction(
        db=db, revision_id=revision_id, service_id=service_id, output_path=location
    )


if __name__ == "__main__":
    app()
