"""
File Attributes Lambda
"""

from aws_lambda_powertools import Tracer
from common_layer.database.client import SqlDB
from common_layer.database.models import (
    OrganisationDatasetRevision,
    OrganisationTXCFileAttributes,
)
from common_layer.database.repos import (
    OrganisationDatasetRevisionRepo,
    OrganisationTXCFileAttributesRepo,
)
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.download import download_and_parse_txc
from common_layer.json_logging import configure_logging
from common_layer.txc.helpers.operator import (
    get_licence_number,
    get_national_operator_code,
)
from common_layer.txc.helpers.service import (
    get_all_line_names,
    get_service_destinations,
    get_service_end_dates,
    get_service_modes,
    get_service_origins,
    get_service_start_dates,
)
from common_layer.txc.models import TXCData
from pydantic import BaseModel, Field
from structlog.stdlib import get_logger

tracer = Tracer()
log = get_logger()


def validate_schema_version(schema_version: str | None) -> str:
    """
    Ensure that the Schema Version is
    """
    if schema_version == "2.4":
        return schema_version
    raise ValueError("SCHEMA_VERSION_NOT_SUPPORTED")


def make_txc_file_attributes(
    txc: TXCData, revision: OrganisationDatasetRevision
) -> OrganisationTXCFileAttributes:
    """
    Construct row data for a TXC File
    """
    metadata = txc.Metadata
    if metadata is None:
        raise ValueError("Missing TXC Metadata")

    start_dates = get_service_start_dates(txc.Services)
    end_dates = get_service_end_dates(txc.Services)

    if len(txc.Services) > 1:
        log.warning("There are more than 1 TXC Service, using first")

    if len(txc.Services) == 0:
        log.error("TXCData does not contain services")
        raise ValueError("TXC Data has no Services")
    modes = get_service_modes(txc.Services)
    if len(modes) > 1:
        log.warning("More than 1 Mode, using first service's", modes=modes)
    if len(modes) == 0:
        log.warning("No Modes found, defaulting to bus")
    return OrganisationTXCFileAttributes(
        schema_version=validate_schema_version(metadata.SchemaVersion),
        modification_datetime=metadata.ModificationDateTime,
        modification=metadata.Modification,
        revision_number=int(metadata.RevisionNumber),
        creation_datetime=metadata.CreationDateTime,
        national_operator_code=get_national_operator_code(txc.Operators) or "",
        licence_number=get_licence_number(txc.Operators) or "",
        line_names=get_all_line_names(txc.Services),
        operating_period_start_date=min(start_dates) if start_dates else None,
        operating_period_end_date=max(end_dates) if end_dates else None,
        origin=next(iter(get_service_origins(txc.Services)), ""),
        destination=next(iter(get_service_destinations(txc.Services)), ""),
        service_code=txc.Services[0].ServiceCode,
        public_use=txc.Services[0].PublicUse,
        filename=metadata.FileName,
        hash=metadata.FileHash or "",
        revision_id=revision.id,
        service_mode=modes[0] if modes else "bus",
    )


class FileAttributesInputData(BaseModel):
    """
    Input data for the ETL Function
    """

    class Config:
        """
        Allow us to map Bucket / Object Key
        """

        populate_by_name = True

    revision_id: int = Field(alias="DatasetRevisionId")
    s3_bucket_name: str = Field(alias="Bucket")
    s3_file_key: str = Field(alias="ObjectKey")


def process_file_attributes(
    input_data: FileAttributesInputData, txc_data: TXCData, db: SqlDB
) -> OrganisationTXCFileAttributes:
    """
    Process the file attributes
    """
    revision = OrganisationDatasetRevisionRepo(db).get_by_id(input_data.revision_id)
    if revision is None:
        log.error("Could not Find Revision by ID", revision_id=input_data.revision_id)
        raise ValueError("Revision ID Not Found")

    file_attributes_data = make_txc_file_attributes(txc_data, revision)
    log.debug(
        "TXC File Attributes Processed", file_attributes_data=file_attributes_data
    )
    return OrganisationTXCFileAttributesRepo(db).insert(file_attributes_data)


@tracer.capture_lambda_handler
@file_processing_result_to_db(StepName.TXC_ATTRIBUTE_EXTRACTION)
def lambda_handler(event, _context) -> dict[str, int]:
    """
    Main lambda handler
    """
    configure_logging()
    input_data = FileAttributesInputData(**event)
    txc_data = download_and_parse_txc(input_data.s3_bucket_name, input_data.s3_file_key)
    db = SqlDB()
    inserted_data = process_file_attributes(input_data, txc_data, db)
    log.info("TXC File Attributes added to database", inserted_data=inserted_data)
    return {"id": inserted_data.id}
