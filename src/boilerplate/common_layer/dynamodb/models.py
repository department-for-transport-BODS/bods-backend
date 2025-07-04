"""
TXC File Attributes Models
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from common_layer.database.models.model_organisation import (
    OrganisationTXCFileAttributes,
)


@dataclass
class TXCFileAttributes:
    """
    TXC File Attributes class used by PTI
    """

    id: int
    revision_number: int
    service_code: str
    line_names: list[str]
    modification_datetime: datetime
    hash: str
    filename: str

    @classmethod
    def from_dict(cls, txcfileattributes: dict[str, Any]) -> TXCFileAttributes:
        """
        Create a TXCFileAttributes instance from a dictionary.
        Converts Unix timestamp to datetime if needed.

        Args:
            txcfileattributes: Dictionary with TXC file attributes, where
            'modification_datetime' is a Unix timestamp (Decimal).

        Returns:
            TXCFileAttributes: A fully populated instance.
        """
        raw_dt: Decimal = txcfileattributes["modification_datetime"]
        txcfileattributes["modification_datetime"] = datetime.fromtimestamp(
            float(raw_dt), tz=timezone.utc
        )
        return cls(**txcfileattributes)

    @staticmethod
    def from_orm(obj: OrganisationTXCFileAttributes):
        """
        Conversion of TXCFileAttributes from DB into the PTI Model
        normalizing modification_datetime by removing microseconds.
        """
        return TXCFileAttributes(
            id=obj.id,
            revision_number=obj.revision_number,
            service_code=obj.service_code,
            line_names=obj.line_names,
            modification_datetime=obj.modification_datetime.replace(microsecond=0),
            hash=obj.hash,
            filename=obj.filename,
        )


@dataclass
class FaresViolation:
    """
    Fares Violation class used to store violation in dynamo
    """

    line: int | None
    observation: str
    category: str
