"""
FOR TEST - Don't run on Postgres DB it is managed by Django

"""

from types import ModuleType
from typing import Type

from sqlalchemy import Column as SQLColumn
from sqlalchemy import Engine, MetaData
from sqlalchemy import Table as SQLTable
from sqlalchemy.sql.schema import Table
from structlog.stdlib import get_logger

from timetables_etl.app.database.models.common import BaseSQLModel

from . import models
from .client import BodsDB

log = get_logger()


def get_model_classes(model_module: ModuleType) -> list[Type[BaseSQLModel]]:
    """Get all SQLAlchemy model classes from models module."""
    return [
        getattr(model_module, attr_name)
        for attr_name in model_module.__all__
        if hasattr(getattr(model_module, attr_name), "__table__")
    ]


def create_table_definition(model: Type[BaseSQLModel], metadata: MetaData) -> SQLTable:
    """Create SQLAlchemy Table definition from model."""
    name = model.__tablename__
    columns = [
        SQLColumn(
            column.key,
            column.type,
            primary_key=column.primary_key,
            nullable=column.nullable,
            index=column.index,
            unique=column.unique,
        )
        for column in model.__table__.columns
    ]

    return SQLTable(name, metadata, *columns, extend_existing=True)


def create_single_table(table: Table, engine: Engine) -> None:
    """Create single table in database."""
    try:
        log.info("Creating table", table_name=table.name)
        table.create(engine, checkfirst=True)
        log.info("Successfully created table", table_name=table.name)
    except Exception as e:
        log.error("Failed to create table", table_name=table.name, error=str(e))
        raise RuntimeError(f"Failed to create table {table.name}: {str(e)}") from e


def create_db_tables(db: BodsDB) -> None:
    """Initialize database tables using models from timetables_etl."""
    log.warning(
        "This function will create tables in postgres. DO NOT do against BODs DB"
    )
    metadata = MetaData()

    model_classes = get_model_classes(models)
    log.info("Models Found", count=len(model_classes))

    tables: list[tuple[str, Table]] = [
        (model.__name__, create_table_definition(model, metadata))
        for model in model_classes
    ]

    for _, table in tables:
        create_single_table(table, db.engine)
