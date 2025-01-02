"""
FOR TEST - Don't run on Real Postgres DB it is managed by Django

This script goes through the SQLAlchemy Models in the models folder and creates them in the DB
Useful for setting up local testing
"""

from types import ModuleType
from typing import Type

from psycopg2 import ProgrammingError
from sqlalchemy import Column as SQLColumn
from sqlalchemy import Engine
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import MetaData
from sqlalchemy import Table as SQLTable
from sqlalchemy import inspect, text
from sqlalchemy.sql.schema import Table
from structlog.stdlib import get_logger

from . import models
from .client import SqlDB
from .models.common import BaseSQLModel

log = get_logger()


def handle_enum_types(engine: Engine, model: Type[BaseSQLModel]) -> None:
    """
    Handle enum types for a given model.
    Ensure the enum type exists and can be used.
    """
    for column in model.__table__.columns:
        if isinstance(column.type, SQLEnum):
            # Preliminary logging of enum type discovery
            log.info(
                "Processing enum type",
                column_name=column.name,
                enum_name=column.type.name,
                model_name=model.__name__,
                enum_values=column.type.enums,
            )

            try:
                with engine.connect() as conn:
                    # Enum name and values from the column type
                    enum_name = column.type.name
                    model_enum_values = column.type.enums

                    # First, create the type if it doesn't exist
                    create_type_query = text(
                        f"""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM pg_type WHERE typname = '{enum_name}'
                            ) THEN
                                CREATE TYPE "{enum_name}" AS ENUM {tuple(model_enum_values)};
                            END IF;
                        END $$;
                    """
                    )
                    conn.execute(create_type_query)

                    log.info(
                        "Ensured enum type exists",
                        enum_name=enum_name,
                        enum_values=model_enum_values,
                    )

                    # Check existing enum values
                    enum_values_query = text(
                        """
                        SELECT unnest(enum_range(NULL::"{enum_name}")) AS enum_value
                    """.format(
                            enum_name=enum_name
                        )
                    )

                    existing_enum_values = list(
                        conn.execute(enum_values_query).scalars().all()
                    )

                    log.info(
                        "Existing enum values discovered",
                        enum_name=enum_name,
                        existing_values=existing_enum_values,
                    )

                    # Find and add missing enum values
                    missing_values = set(model_enum_values) - set(existing_enum_values)

                    if missing_values:
                        log.warning(
                            "Missing enum values detected",
                            enum_name=enum_name,
                            missing_values=list(missing_values),
                            existing_values=existing_enum_values,
                        )

                        for value in missing_values:
                            try:
                                alter_type_query = text(
                                    f"ALTER TYPE \"{enum_name}\" ADD VALUE '{value}'"
                                )
                                conn.execute(alter_type_query)

                                log.info(
                                    "Added missing enum value",
                                    enum_name=enum_name,
                                    added_value=value,
                                    model_name=model.__name__,
                                )
                            except Exception as add_value_error:
                                log.warning(
                                    "Failed to add enum value",
                                    enum_name=enum_name,
                                    attempted_value=value,
                                    error=str(add_value_error),
                                    model_name=model.__name__,
                                )
                    else:
                        log.info(
                            "No missing enum values - all values present",
                            enum_name=enum_name,
                            existing_values=existing_enum_values,
                        )

                    # Override the create method to prevent recreation
                    column.type.create = lambda *args, **kwargs: None

                    log.info(
                        "Enum type handling completed",
                        enum_name=enum_name,
                        final_values=model_enum_values,
                        model_name=model.__name__,
                    )

            except Exception as e:
                log.error(
                    "Critical error in enum type handling",
                    enum_name=column.type.name,
                    model_name=model.__name__,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise


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


def create_table_definition(model: Type[BaseSQLModel], metadata: MetaData) -> SQLTable:
    """
    Create SQLAlchemy Table definition from model.

    Modifies column creation to handle enum types more carefully,
    preventing duplicate enum type creation.
    """
    name = model.__tablename__
    columns = []

    log.info(
        "Creating table definition",
        model_name=model.__name__,
        table_name=name,
        total_columns=len(model.__table__.columns),
    )

    for column in model.__table__.columns:
        # Preliminary column logging
        column_log_data = {
            "column_name": column.key,
            "column_type": str(column.type),
            "is_primary_key": column.primary_key,
            "is_nullable": column.nullable,
            "has_index": column.index,
            "is_unique": column.unique,
        }

        # Special handling for Enum types
        if isinstance(column.type, SQLEnum):
            log.info(
                "Processing enum column",
                **column_log_data,
                enum_name=column.type.name,
                enum_values=column.type.enums,
            )

            # Override the create method to prevent recreation
            column.type.create = lambda *args, **kwargs: None

            log.debug(
                "Disabled enum type recreation (handled in the handle enum types)",
                enum_name=column.type.name,
            )

        # Create the column with modified type
        try:
            column_def = SQLColumn(
                column.key,
                column.type,
                primary_key=column.primary_key,
                nullable=column.nullable,
                index=column.index,
                unique=column.unique,
            )
            columns.append(column_def)

            log.debug("Added column to table definition", **column_log_data)
        except Exception as e:
            log.error(
                "Failed to create column definition",
                **column_log_data,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    log.info(
        "Table definition created successfully",
        model_name=model.__name__,
        table_name=name,
        total_columns=len(columns),
    )

    return SQLTable(name, metadata, *columns, extend_existing=True)


def create_single_table(table: Table, engine: Engine) -> None:
    """Create single table in database."""
    inspector = inspect(engine)

    if inspector.has_table(table.name):
        raise RuntimeError(f"Table {table.name} already exists")

    try:
        log.info("Creating table", table_name=table.name)
        table.create(engine, checkfirst=False)
        log.info("Successfully created table", table_name=table.name)
    except Exception as e:
        log.error("Failed to create table", table_name=table.name, error=str(e))
        raise RuntimeError(f"Failed to create table {table.name}: {str(e)}") from e


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

    for model in model_classes:
        handle_enum_types(db.engine, model)
        table = create_table_definition(model, metadata)

        # First try to create the table
        try:
            create_single_table(table, db.engine)
        except Exception:
            log.info(
                "Table already exists, checking for column updates", table=table.name
            )
            # If table exists, check and update columns
            compare_and_alter_table(model, table, db.engine)
