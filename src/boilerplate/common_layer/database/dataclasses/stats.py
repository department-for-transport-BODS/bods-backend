from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class RevisionStats:
    publisher_creation_datetime: datetime | None = None
    publisher_modification_datetime: datetime | None = None
    first_expiring_service: date | None = None
    last_expiring_service: date | None = None
    first_service_start: date | None = None


@dataclass
class ServiceStats:
    first_service_start: date | None
    first_expiring_service: date | None
    last_expiring_service: date | None


@dataclass
class TXCFileStats:
    first_creation_datetime: datetime | None
    last_modification_datetime: datetime | None
