"""
TXC File Metadata
"""

from lxml.etree import _Element
from structlog.stdlib import get_logger

from ..models.txc_metadata import TXCMetadata
from .utils_attributes import (
    parse_creation_datetime,
    parse_modification,
    parse_modification_datetime,
)

log = get_logger()


def parse_revision_number(xml_data: _Element) -> int:
    """
    Parse revision into an int
    """
    revision_number = xml_data.get("RevisionNumber")
    if revision_number is None:
        log.error("Revision Number is missing")
        raise ValueError("Revision Number is required in TXC Documents")
    try:
        return int(revision_number)
    except ValueError:
        log.error("Revision Number cannot be parsed", revision_number=revision_number)
        raise


def parse_metadata(
    xml_data: _Element, file_hash: str | None = None
) -> TXCMetadata | None:
    """Parse metadata from XML, returning None if required fields are missing."""
    schema_version = xml_data.get("SchemaVersion")

    file_name = xml_data.get("FileName")
    modification_dt = parse_modification_datetime(xml_data)
    creation_dt = parse_creation_datetime(xml_data)
    modification = parse_modification(xml_data)

    try:
        revision_number = parse_revision_number(xml_data)
    except ValueError:
        return None
    if (
        schema_version is None
        or file_name is None
        or modification_dt is None
        or creation_dt is None
        or modification is None
    ):
        log.error("Required Metadata Missing in TXC File")
        return None

    return TXCMetadata(
        SchemaVersion=schema_version,
        ModificationDateTime=modification_dt,
        Modification=modification,
        RevisionNumber=revision_number,
        CreationDateTime=creation_dt,
        FileName=file_name,
        RegistrationDocument=bool(xml_data.get("RegistrationDocument")),
        FileHash=file_hash,
    )
