from typing import List, Set
from structlog.stdlib import get_logger
import typer
from common_layer.database.repos import (
    OrganisationDatasetRevisionRepo,
    OrganisationTXCFileAttributesRepo,
    TransmodelServiceRepo,
    TransmodelServicePatternRepo,
    TransmodelServicePatternStopRepo,
    TransmodelVehicleJourneyRepo
)

from .utils import *

logger = get_logger()
app = typer.Typer()


def get_organisation_datasetrevision_csv(db: SqlDB,
                                         revision_id: int,
                                         output_path: Path | None = None):
    try:
        revision_instance = OrganisationDatasetRevisionRepo(db)
        result_revision = revision_instance.get_by_id(revision_id)
        buffer = model_to_csv([result_revision],
                              output_dir=output_path)
        return buffer
    except Exception as e:
        logger.error(f"Could not able to generate csv for "
                     f"organisation_datasetrevision {e}")
        raise e


def get_organisation_txcfileattributes_csv(db: SqlDB,
                                           revision_id: int,
                                           output_path: Path | None = None):
    try:
        revision_instance = OrganisationTXCFileAttributesRepo(db)
        txcfileattributes = revision_instance.get_by_revision_id(revision_id)
        buffer = model_to_csv(txcfileattributes, output_dir=output_path)
        return buffer
    except Exception as e:
        logger.error(f"Could not able to generate csv for "
                     f"organisation_txcfileattributes {e}")
        raise e


def get_transmodel_service_csv(db: SqlDB,
                               revision_id: int,
                               output_path: Path | None = None):
    try:
        revision_instance = TransmodelServiceRepo(db)
        transmodel_service = revision_instance.get_by_revision_id(revision_id)
        buffer = model_to_csv(transmodel_service, output_dir=output_path)
        return buffer
    except Exception as e:
        logger.error(f"Could not able to generate csv for "
                     f"transmodel_service {e}")
        raise e

def get_transmodel_servicepattern_csv(db: SqlDB,
                                      revision_id: int,
                                      output_path: Path | None = None):
    try:
        revision_instance = TransmodelServicePatternRepo(db)
        service_patterns = revision_instance.get_by_revision_id(revision_id)
        pattern_ids = [item.id for item in service_patterns]
        model_to_csv(service_patterns, output_dir=output_path)
        return pattern_ids
    except Exception as e:
        logger.error(f"Could not able to generate csv for "
                     f"transmodel_servicepattern {e}")
        raise e


def get_transmodel_servicepatternstop_csv(db: SqlDB,
                                          service_pattern_ids:
                                          List[int] | Set[int],
                                          output_path: Path | None = None):
    try:
        revision_instance = TransmodelServicePatternStopRepo(db)
        service_pattern_stops = revision_instance.get_by_service_pattern_ids(
            service_pattern_ids)
        vehicle_journey_ids = [it.vehicle_journey_id
                               for it in service_pattern_stops]
        model_to_csv(service_pattern_stops, output_dir=output_path)
        return vehicle_journey_ids
    except Exception as e:
        logger.error(f"Could not able to generate csv for "
                     f"transmodel_servicepatternstop {e}")
        raise e


def get_transmodel_vehiclejourney_csv(db: SqlDB,
                                      vehicle_journey_ids: List[int] | Set[int],
                                      output_path: Path | None = None):
    try:
        vehicle_journey = TransmodelVehicleJourneyRepo(db)
        vehicle_journeys = vehicle_journey.get_by_ids(
            vehicle_journey_ids)
        buffer = model_to_csv(vehicle_journeys, output_dir=output_path)
        return buffer
    except Exception as e:
        logger.error(f"Could not able to generate csv for "
                     f"transmodel_vehiclejourney {e}")
        raise e


@app.command()
def main(
        location: Path = typer.Option(
        None,
        "--dir",
        help="Paths to csv files",
        ),
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
            "--revision-id",
            help="Dataset revision id",
        ),
):
    config = DbConfig(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
    )
    db = get_db_instance(config)
    get_organisation_datasetrevision_csv(db,
                                         revision_id=revision_id,
                                         output_path=location)
    get_organisation_txcfileattributes_csv(db,
                                           revision_id=revision_id,
                                           output_path=location)
    get_transmodel_service_csv(db,
                               revision_id=revision_id,
                               output_path=location)
    _ids = get_transmodel_servicepattern_csv(db,
                                             revision_id=revision_id,
                                             output_path=location)

    vehicle_journey_ids = get_transmodel_servicepatternstop_csv(db,
                                                                set(_ids),
                                                                location)
    get_transmodel_vehiclejourney_csv(db, set(vehicle_journey_ids), location)


if __name__ == "__main__":
    app()
