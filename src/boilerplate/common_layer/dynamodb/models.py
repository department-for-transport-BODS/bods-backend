from dataclasses import dataclass
from datetime import datetime

from common_layer.database.models.model_organisation import (
    OrganisationTXCFileAttributes,
)


@dataclass
class TXCFileAttributes:
    id: int
    revision_number: int
    service_code: str
    line_names: list[str]
    modification_datetime: datetime
    hash: str
    filename: str

    @staticmethod
    def from_orm(obj: OrganisationTXCFileAttributes):
        return TXCFileAttributes(
            id=obj.id,
            revision_number=obj.revision_number,
            service_code=obj.service_code,
            line_names=obj.line_names,
            modification_datetime=obj.modification_datetime,
            hash=obj.hash,
            filename=obj.filename,
        )
