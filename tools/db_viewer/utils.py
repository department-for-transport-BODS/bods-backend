from csv import DictWriter, QUOTE_MINIMAL
from datetime import datetime, date, time
from dataclasses import is_dataclass, fields
from decimal import Decimal
from uuid import UUID
from io import StringIO
from pathlib import Path
from typing import Any
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from structlog.stdlib import get_logger
from common_layer.database.models.common import BaseSQLModel
from common_layer.database.client import (
    DatabaseBackend,
    DatabaseSettings,
    PostgresSettings,
    SqlDB
)
from .config import DbConfig
logger = get_logger()


def get_db_instance(config: DbConfig) -> SqlDB:
    """Initialize database connection"""
    pg_settings = PostgresSettings(
        POSTGRES_HOST=config.host,
        POSTGRES_DB=config.database,
        POSTGRES_USER=config.user,
        POSTGRES_PASSWORD=config.password,
        POSTGRES_PORT=config.port,
    )
    settings = DatabaseSettings(
        postgres=pg_settings,
    )
    return SqlDB(DatabaseBackend.POSTGRESQL, settings)


def model_to_dict(instance: BaseSQLModel) -> dict:
    if is_dataclass(instance):
        result: dict[str, Any] = {}
        for column in fields(instance):
            if not column.name.startswith('_'):
                value = getattr(instance, column.name)
                match value:
                    case date():
                        value = value.isoformat()
                    case time():
                        value = value.isoformat()
                    case datetime():
                        value = value.isoformat()
                    case WKBElement():
                        value = to_shape(value).wkt
                    case Decimal():
                        value = str(value)
                    case UUID():
                        value = str(value)
                result[column.name] = value
        return result

    raise TypeError(f"Expected dataclass, got {type(instance)}")


def model_to_csv(instances, output_dir=None, delimiter=',', include_header=True):
    if not instances:
        raise ValueError("Cannot convert empty sequence to CSV")

    records = [model_to_dict(instance) for instance in instances]
    column_names = list(records[0].keys())
    full_path = Path(f"{instances[0].__tablename__}.csv")
    logger.info(f"Table {instances[0].__tablename__}")
    if output_dir:
        output_dir = output_dir if isinstance(output_dir, Path) \
            else Path(output_dir)
        full_path = output_dir / full_path
    logger.info(f"Writing CSV to {full_path}")

    with StringIO() as output:
        writer = DictWriter(
            output,
            fieldnames=column_names,
            delimiter=delimiter,
            quoting=QUOTE_MINIMAL,
            lineterminator="\n",
        )
        if include_header:
            writer.writeheader()
        writer.writerows(records)
        csv_content = output.getvalue()
    try:
        full_path.write_text(csv_content, encoding="utf-8")
    except OSError as e:
        raise OSError(f"Failed to write CSV to {full_path}: {e}") from e
    return csv_content
