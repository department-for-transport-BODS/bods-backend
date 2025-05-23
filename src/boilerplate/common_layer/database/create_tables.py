"""
FOR TEST - Don't run on Real Postgres DB it is managed by Django

This script goes through the SQLAlchemy Models in the models folder and creates them in the DB
Useful for setting up local testing
"""

from types import ModuleType
from typing import Any, Type, cast

import structlog
from sqlalchemy import Column as SQLColumn
from sqlalchemy import Engine, MetaData, UniqueConstraint, inspect, text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.engine.interfaces import ReflectedColumn
from sqlalchemy.sql.schema import Table
from sqlalchemy.types import Enum as SQLEnumType
from structlog.stdlib import get_logger

from . import models
from .client import SqlDB
from .models.common import BaseSQLModel

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ]
)

log = get_logger()


def get_existing_columns(engine: Engine, table_name: str) -> dict[str, ReflectedColumn]:
    """Get existing columns from database table."""
    inspector = inspect(engine)
    columns: dict[str, ReflectedColumn] = {}

    if inspector.has_table(table_name):
        for column in inspector.get_columns(table_name):
            columns[column["name"]] = column

    return columns


def get_existing_constraints(engine: Engine, table_name: str) -> list[str]:
    """Get existing constraint names from a database table."""
    inspector = inspect(engine)
    constraints: list[str] = []

    if inspector.has_table(table_name):
        # Get unique constraints
        unique_constraints = inspector.get_unique_constraints(table_name)
        for c in unique_constraints:
            if c["name"] is not None:
                constraints.append(c["name"])

        # Get primary key constraints
        pk = inspector.get_pk_constraint(table_name)
        pk_name = pk.get("name")
        if pk_name is not None:
            constraints.append(pk_name)

        # Get foreign key constraints
        fk_constraints = inspector.get_foreign_keys(table_name)
        for fk in fk_constraints:
            fk_name = fk.get("name")
            if fk_name is not None:
                constraints.append(fk_name)

    return constraints


def extract_table_args(model: Type[BaseSQLModel]) -> tuple[Any, ...]:
    """
    Extract table arguments including constraints from a SQLAlchemy model.
    Returns a tuple of table arguments that can be passed to Table constructor.
    """
    table_args = cast(
        tuple[Any, ...] | dict[str, Any], getattr(model, "__table_args__", ())
    )
    # If table_args is a dict, it's not constraints but table options
    # In that case, return an empty tuple as we're only interested in constraints here
    if isinstance(table_args, dict):
        log.info(
            "Model has table options but no constraints",
            model_name=model.__name__,
            options=table_args,
        )
        return ()

    # If it's a tuple, it might contain constraints and/or a dict of table options
    # Filter out the dict of options if present (usually the last item)
    constraints: list[Any] = []
    for item in table_args:
        if not isinstance(item, dict):
            constraints.append(item)

    if constraints:
        log.info(
            "Extracted table constraints",
            model_name=model.__name__,
            constraint_count=len(constraints),
            constraint_types=[type(c).__name__ for c in constraints],
        )
        return tuple(constraints)

    return ()


def add_missing_constraints(
    model: Type[BaseSQLModel], table_name: str, engine: Engine
) -> None:
    """Add missing constraints to an existing table."""
    # Extract table constraints from model
    table_constraints = extract_table_args(model)
    if not table_constraints:
        return

    # Get existing constraint names
    existing_constraints = get_existing_constraints(engine, table_name)

    for constraint in table_constraints:
        # Skip constraints without names
        if not hasattr(constraint, "name") or not constraint.name:
            continue

        # Check if constraint already exists
        if constraint.name in existing_constraints:
            continue

        log.info(
            "Adding missing constraint to table",
            table=table_name,
            constraint_name=constraint.name,
            constraint_type=type(constraint).__name__,
        )

        try:
            # Handle different constraint types
            if isinstance(constraint, UniqueConstraint):
                # Get column names from the constraint
                columns = ", ".join([f'"{col}"' for col in constraint.columns])

                # Create ALTER TABLE statement for unique constraint
                alter_stmt = (
                    f'ALTER TABLE "{table_name}" '
                    f'ADD CONSTRAINT "{constraint.name}" UNIQUE ({columns})'
                )

                with engine.begin() as conn:
                    conn.execute(text(alter_stmt))

                log.info(
                    "Successfully added unique constraint",
                    table=table_name,
                    constraint_name=constraint.name,
                )

            # Add other constraint types as needed (ForeignKeyConstraint, CheckConstraint, etc.)
            else:
                log.warning(
                    "Unsupported constraint type for automatic addition",
                    table=table_name,
                    constraint_name=constraint.name,
                    constraint_type=type(constraint).__name__,
                )

        except Exception as e:  # pylint: disable=broad-exception-caught
            log.error(
                "Failed to add constraint",
                table=table_name,
                constraint_name=constraint.name,
                error=str(e),
            )


def compare_and_alter_table(
    model: Type[BaseSQLModel], table: Table, engine: Engine
) -> None:
    """
    Compare existing table columns with model columns and alter table if needed.
    Also adds any missing constraints defined in the model.
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
                alter_stmt = (
                    f'ALTER TABLE "{table.name}" '
                    f'ADD COLUMN "{column.name}" {compiled_type}'
                )

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

    # Add any missing constraints defined in the model
    add_missing_constraints(model, table.name, engine)


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

        # (type stub says it's a list[Unknown]) so need to ignore in strict
        enum_values: tuple[str, ...] = tuple(enum_type.enums)  # type: ignore

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
    column: SQLColumn[Any], enum_info: tuple[str, tuple[str, ...]] | None = None
) -> SQLColumn[Any]:
    """
    Create a SQLAlchemy column definition, handling both enum and standard columns
    """
    log_context: dict[str, str | bool | None] = {
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
    with proper column definitions including enum references and table constraints.
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

    # Create column definitions
    columns = create_table_columns(model, enum_types)

    # Extract table constraints and other table arguments
    table_constraints = extract_table_args(model)

    log.info(
        "Attempting to create table",
        model_name=model.__name__,
        table_name=table_name,
        total_columns=len(columns),
        constraint_count=len(table_constraints),
    )

    table = Table(table_name, metadata, *columns, *table_constraints)
    try:
        table.create(engine)
        log.info(
            "Successfully created table",
            model_name=model.__name__,
            table_name=table_name,
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        log.warning(
            "Table creation failed, checking if table exists",
            model_name=model.__name__,
            table_name=table_name,
            error=str(e),
            error_type=type(e).__name__,
        )
        compare_and_alter_table(model, table, engine)


def enable_postgis_extension(engine: Engine):
    """
    PostGIS is used for LineString in tables
    It's an extension that needs to be installed on the machine running postgres
    And then for every database inside the postgres server, it needs to be enabled
    """
    postgis_stmt = "CREATE EXTENSION IF NOT EXISTS postgis;"
    with engine.begin() as conn:
        conn.execute(text(postgis_stmt))


def create_db_tables(db: SqlDB | None = None) -> None:
    """Initialize database tables using models from timetables_etl."""
    log.warning(
        "Creating Tables: This function will create tables in postgres. DO NOT do against BODs DB"
    )
    if db is None:
        db = SqlDB()
    metadata = MetaData()

    enable_postgis_extension(db.engine)

    model_classes = get_model_classes(models)
    log.info(
        "Models Found",
        count=len(model_classes),
        models=[cls.__name__ for cls in model_classes],
    )

    # Sort models to ensure consistent creation order
    sorted_models = sorted(model_classes, key=lambda m: m.__name__)

    for model in sorted_models:
        handle_enums_and_create_table(model, metadata, db.engine)
