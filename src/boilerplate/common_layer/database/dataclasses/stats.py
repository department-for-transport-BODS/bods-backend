from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class RevisionStats:
    """
    Summary stats for a Dataset Revision
    """

    publisher_creation_datetime: datetime | None = None
    publisher_modification_datetime: datetime | None = None
    first_expiring_service: date | None = None
    last_expiring_service: date | None = None
    first_service_start: date | None = None


@dataclass
class ServiceStats:
    """
    Summary stats for a group of Services
    """

    first_service_start: date | None
    first_expiring_service: date | None
    last_expiring_service: date | None


@dataclass
class TXCFileStats:
    """
    Summary stats for a group of TXC File Attributes
    """

    first_creation_datetime: datetime | None
    last_modification_datetime: datetime | None
