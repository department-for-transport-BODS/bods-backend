"""
DynamoDB Utils
"""

from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any, TypeGuard

from .models import TXCFileAttributes

TXCValue = int | str | list[str] | datetime
TXCDictValue = int | str | list[str]


def is_dataclass_instance(obj: Any) -> TypeGuard[TXCFileAttributes]:
    """Check if object is a TXCFileAttributes instance"""
    return is_dataclass(obj) and isinstance(obj, TXCFileAttributes)


def serialize_value(value: TXCValue) -> TXCDictValue:
    """
    Serialize Values specific to TXCFileAttributes fields
    """
    if isinstance(value, datetime):
        return int(value.timestamp())
    if isinstance(value, list):
        return value
    return value


def dataclass_to_dict(obj: TXCFileAttributes) -> dict[str, TXCDictValue]:
    """Convert a TXCFileAttributes instance to a dictionary converting datetimes to timestamps"""
    if not is_dataclass_instance(obj):
        raise TypeError("Input must be a TXCFileAttributes instance")

    return {key: serialize_value(value) for key, value in asdict(obj).items()}
