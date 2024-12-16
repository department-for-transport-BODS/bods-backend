"""
Utility functions to support db viwer tool
"""

from csv import DictWriter, QUOTE_MINIMAL
from datetime import datetime, date, time
from dataclasses import is_dataclass, fields
from decimal import Decimal
from functools import wraps
from uuid import UUID
from io import StringIO
from pathlib import Path
from typing import Any, Callable, ParamSpec, TypeVar, cast
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from structlog.stdlib import get_logger
from common_layer.database.models.common import BaseSQLModel
from common_layer.database.client import (
    DatabaseBackend,
    DatabaseSettings,
    PostgresSettings,
    SqlDB,
)
from .config import DbConfig

logger = get_logger()

P = ParamSpec("P")
T = TypeVar("T")


class DatasetRevisionNotFoundError(Exception):
    """
    Raised when a dataset revision cannot be found.
    """

    def __init__(self, revision_id: int):
        super().__init__(f"Dataset revision {revision_id} not found")


def csv_extractor():
    """
    Decorator that handles CSV extraction logic.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(db: SqlDB, *args: Any, output_path: Path | None = None) -> T:
            log = logger.bind(
                operation="CSV Data Extraction and Output", function=func.__name__
            )
            try:
                log.info("Querying DB", args=args)
                results = func(db, *args)
                if isinstance(results, list):
                    log.info("Got DB Results", result_count=len(results))
                if results:
                    model_to_csv(
                        [results] if not isinstance(results, list) else results,  # type: ignore
                        output_dir=output_path,
                    )
                    log.info("Outputted Data to CSV", output_path=str(output_path))
                else:
                    log.warning("No Data to generate CSV")

                return cast(T, results)
            except Exception as e:
                log.error(
                    "Failed to Generate CSV", error=str(e), error_type=type(e).__name__
                )
                raise

        return wrapper

    return decorator


def get_db_instance(config: DbConfig) -> SqlDB:
    """Initialize and get database instance"""
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
    """
    Convert model data into dictionary
    """
    if is_dataclass(instance):
        result: dict[str, Any] = {}
        for column in fields(instance):
            if not column.name.startswith("_"):
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


def model_to_csv(
    instances: list[BaseSQLModel],
    output_dir: Path | str | None = None,
    delimiter: str = ",",
    include_header: bool = True,
) -> str:
    """
    Extract/Create the CSV file
    """
    if not instances:
        raise ValueError("Cannot convert empty sequence to CSV")

    records = [model_to_dict(instance) for instance in instances]
    column_names = list(records[0].keys())
    full_path = Path(f"{instances[0].__tablename__}.csv")
    logger.info(f"Table {instances[0].__tablename__}")

    # Handle the output directory
    if output_dir:
        output_dir = output_dir if isinstance(output_dir, Path) else Path(output_dir)
        full_path = output_dir / full_path

        # Expand the home directory symbol (~) if it exists
        if "~" in str(full_path):
            full_path = full_path.expanduser()

        # If the path is relative, resolve it to an absolute path
        if not full_path.is_absolute():
            full_path = full_path.resolve()

        # Ensure the parent directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing CSV to file", path=full_path)

    # Write to CSV
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

    # Return CSV content
    return csv_content
