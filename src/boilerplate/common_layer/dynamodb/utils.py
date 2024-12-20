from dataclasses import asdict, is_dataclass
from datetime import datetime


def dataclass_to_dict(obj):
    """Convert a dataclass to a dictionary, converting datetimes to timestamps for storing in dynamo."""

    def serialize_value(value):
        if isinstance(value, datetime):
            return int(value.timestamp())
        elif is_dataclass(value):
            return dataclass_to_dict(value)
        elif isinstance(value, list):
            return [serialize_value(item) for item in value]
        return value

    return {key: serialize_value(value) for key, value in asdict(obj).items()}
