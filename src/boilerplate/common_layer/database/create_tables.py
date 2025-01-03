"""
FOR TEST - Don't run on Real Postgres DB it is managed by Django

This script goes through the SQLAlchemy Models in the models folder and creates them in the DB
Useful for setting up local testing
"""

from types import ModuleType
from typing import Any, Type, cast

from sqlalchemy import Column as SQLColumn
from sqlalchemy import Engine, MetaData, inspect, text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.sql.schema import Table
from sqlalchemy.types import Enum as SQLEnumType
from structlog.stdlib import get_logger

from . import models
from .client import SqlDB
from .models.common import BaseSQLModel

log = get_logger()


def get_existing_columns(engine: Engine, table_name: str) -> dict[str, SQLColumn]:
    """Get existing columns from database table."""
    inspector = inspect(engine)
    columns = {}

    if inspector.has_table(table_name):
        for column in inspector.get_columns(table_name):
            columns[column["name"]] = column

    return columns


def compare_and_alter_table(
    model: Type[BaseSQLModel], table: Table, engine: Engine
) -> None:
    """
    Compare existing table columns with model columns and alter table if needed.
    TODO: IF columns are NOT NULL and existing rows are there, this will fail
    """
    inspector = inspect(engine)
    existing_columns = get_existing_columns(engine, table.name)
    model_columns = {col.name: col for col in model.__table__.columns}
    if not inspector.has_table(table.name):
        log.warning(
            "Table does not exist, skipping column comparison", table=table.name
        )
        return
    # Find missing columns (in DB but not in model)
    missing_in_model = set(existing_columns.keys()) - set(model_columns.keys())
    if missing_in_model:
        log.warning(
            "Columns exist in database but not in model",
            table=table.name,
            columns=list(missing_in_model),
        )

    # Find new columns (in model but not in DB)
    new_columns = set(model_columns.keys()) - set(existing_columns.keys())
    if new_columns:
        log.warning(
            "New columns found in model - will alter table",
            table=table.name,
            new_columns=list(new_columns),
        )

        # Add each new column
        for col_name in new_columns:
            column = model_columns[col_name]
            try:
                compiled_type = column.type.compile(engine.dialect)
                # Generate ALTER TABLE statement
                alter_stmt = f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {compiled_type}'

                # Add nullable constraint if specified
                if not column.nullable:
                    alter_stmt += " NOT NULL"

                # Add unique constraint if specified
                if column.unique:
                    alter_stmt += " UNIQUE"

                # Execute the alter statement
                with engine.begin() as conn:
                    conn.execute(text(alter_stmt))

                log.info(
                    "Successfully added new column",
                    table=table.name,
                    column=column.name,
                )

            except Exception as e:
                log.error(
                    "Failed to add column",
                    table=table.name,
                    column=column.name,
                    error=str(e),
                )
                raise RuntimeError(
                    f"Failed to add column {column.name} to table {table.name}: {str(e)}"
                ) from e


def get_model_classes(model_module: ModuleType) -> list[Type[BaseSQLModel]]:
    """Get all SQLAlchemy model classes from models module."""
    return [
        getattr(model_module, attr_name)
        for attr_name in model_module.__all__
        if hasattr(getattr(model_module, attr_name), "__table__")
    ]


def check_enum_exists(engine: Engine, enum_name: str) -> bool:
    """
    Check if a PostgreSQL enum type already exists in the database
    """
    with engine.connect() as conn:
        check_type_query = text("SELECT 1 FROM pg_type WHERE typname = :enum_name")
        return (
            conn.execute(check_type_query, {"enum_name": enum_name}).scalar()
            is not None
        )


def create_enum_type(
    engine: Engine, enum_name: str, enum_values: tuple[str, ...]
) -> None:
    """
    Create a new PostgreSQL enum type in the database
    """
    try:
        with engine.connect() as conn:
            create_type_query = text(
                f'CREATE TYPE "{enum_name}" AS ENUM {enum_values};'
            )
            conn.execute(create_type_query)
            conn.commit()
            log.info(
                "Successfully created enum type",
                enum_name=enum_name,
                enum_values=enum_values,
            )
    except Exception as e:
        log.error(
            "Failed to create enum type",
            enum_name=enum_name,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise


def get_enum_info(
    model: Type[BaseSQLModel], table_name: str
) -> dict[str, tuple[str, tuple[str, ...]]]:
    """
    Extract enum information from a SQLAlchemy model's columns.
    Returns a mapping of column names to their enum type information.
    """
    enum_columns = [
        col for col in model.__table__.columns if isinstance(col.type, SQLEnumType)
    ]

    if not enum_columns:
        return {}

    log.info(
        "Found enum columns",
        model_name=model.__name__,
        enum_count=len(enum_columns),
        column_names=[col.key for col in enum_columns],
    )

    enum_types: dict[str, tuple[str, tuple[str, ...]]] = {}
    for column in enum_columns:
        enum_type = cast(SQLEnumType, column.type)
        # Handle the case where name might be None
        if enum_type.name:
            enum_name = enum_type.name.lower()
        else:
            # Fallback to generating a name based on table and column
            enum_name = f"{table_name}_{column.key}_enum"

        enum_values = tuple(enum_type.enums)

        log.info(
            "Processing enum column",
            model_name=model.__name__,
            column_name=column.key,
            enum_name=enum_name,
            enum_values=enum_values,
        )
        enum_types[column.key] = (enum_name, enum_values)

    return enum_types


def create_column_definition(
    column: SQLColumn, enum_info: tuple[str, tuple[str, ...]] | None = None
) -> SQLColumn:
    """
    Create a SQLAlchemy column definition, handling both enum and standard columns
    """
    log_context = {
        "column_name": column.key,
        "column_type": str(column.type),
        "is_enum": enum_info is not None,
        "is_primary_key": column.primary_key,
        "is_nullable": column.nullable,
        "has_index": column.index,
        "is_unique": column.unique,
    }

    log.info("Creating column definition", **log_context)

    try:
        if enum_info:
            enum_name, enum_values = enum_info
            return SQLColumn(
                column.key,
                ENUM(*enum_values, name=enum_name, create_type=False),
                primary_key=column.primary_key,
                nullable=column.nullable,
                index=column.index,
                unique=column.unique,
            )
        else:
            return SQLColumn(
                column.key,
                column.type,
                primary_key=column.primary_key,
                nullable=column.nullable,
                index=column.index,
                unique=column.unique,
            )
    except Exception as e:
        log.error(
            "Failed to create column definition",
            **log_context,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise


def create_table_columns(
    model: Type[BaseSQLModel], enum_types: dict[str, tuple[str, tuple[str, ...]]]
) -> list[SQLColumn[Any]]:
    """
    Create all column definitions for a table, properly handling column types
    """
    columns: list[SQLColumn[Any]] = []

    for column in model.__table__.columns:
        typed_column = cast(SQLColumn[Any], column)
        enum_info = enum_types.get(column.key)
        column_def = create_column_definition(typed_column, enum_info)
        columns.append(column_def)

    return columns


def handle_enums_and_create_table(
    model: Type[BaseSQLModel], metadata: MetaData, engine: Engine
) -> None:
    """
    Create a database table for a SQLAlchemy model, handling PostgreSQL enum types.
    First creates any required enum types if they don't exist, then creates the table
    with proper column definitions including enum references
    """
    table_name = model.__tablename__
    log.info(
        "Starting table creation process",
        model_name=model.__name__,
        table_name=table_name,
        is_abstract=getattr(model, "__abstract__", False),
    )

    # Handle enum types
    enum_types = get_enum_info(model, table_name)
    for enum_name, enum_values in enum_types.values():
        if not check_enum_exists(engine, enum_name):
            create_enum_type(engine, enum_name, enum_values)

    columns = create_table_columns(model, enum_types)

    # Create table
    log.info(
        "Attempting to create table",
        model_name=model.__name__,
        table_name=table_name,
        total_columns=len(columns),
    )

    table = Table(table_name, metadata, *columns)
    try:
        table.create(engine)
        log.info(
            "Successfully created table",
            model_name=model.__name__,
            table_name=table_name,
        )
    except Exception as e:
        log.warning(
            "Table creation failed, checking if table exists",
            model_name=model.__name__,
            table_name=table_name,
            error=str(e),
            error_type=type(e).__name__,
        )
        compare_and_alter_table(model, table, engine)


def create_db_tables(db: SqlDB | None = None) -> None:
    """Initialize database tables using models from timetables_etl."""
    log.warning(
        "Creating Tables: This function will create tables in postgres. DO NOT do against BODs DB"
    )
    if db is None:
        db = SqlDB()
    metadata = MetaData()

    model_classes = get_model_classes(models)
    log.info("Models Found", count=len(model_classes))

    # Sort models to ensure consistent creation order
    sorted_models = sorted(model_classes, key=lambda m: m.__name__)

    for model in sorted_models:
        if getattr(model, "__abstract__", False):
            continue
        handle_enums_and_create_table(model, metadata, db.engine)
