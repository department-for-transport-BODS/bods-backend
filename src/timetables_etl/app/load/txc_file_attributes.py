"""
Generation of a TXC File Attributes from a TXC File
"""

from structlog.stdlib import get_logger

from ..database.models.model_organisation import (
    OrganisationDatasetRevision,
    OrganisationTXCFileAttributes,
)
from ..txc.helpers.operator import get_licence_number, get_national_operator_code
from ..txc.helpers.service import (
    get_line_names,
    get_service_destinations,
    get_service_end_dates,
    get_service_origins,
    get_service_start_dates,
)
from ..txc.models import TXCData

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

    return OrganisationTXCFileAttributes(
        schema_version=validate_schema_version(metadata.SchemaVersion),
        modification_datetime=metadata.ModificationDateTime,
        modification=metadata.Modification,
        revision_number=int(metadata.RevisionNumber),
        creation_datetime=metadata.CreationDateTime,
        national_operator_code=get_national_operator_code(txc.Operators) or "",
        licence_number=get_licence_number(txc.Operators) or "",
        line_names=get_line_names(txc.Services),
        operating_period_start_date=min(start_dates) if start_dates else None,
        operating_period_end_date=max(end_dates) if end_dates else None,
        origin=next(iter(get_service_origins(txc.Services)), ""),
        destination=next(iter(get_service_destinations(txc.Services)), ""),
        service_code=txc.Services[0].ServiceCode,
        public_use=txc.Services[0].PublicUse,
        filename=metadata.FileName,
        hash=metadata.FileHash or "",
        revision_id=revision.id,
    )
