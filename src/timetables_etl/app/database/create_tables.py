"""
FOR TEST - Don't run on Postgres DB it is managed by Django

"""

from sqlalchemy import Column, MetaData, Table
from structlog.stdlib import get_logger

from . import models
from .client import BodsDB, DatabaseBackend

log = get_logger()


def create_db_tables(db: BodsDB) -> None:
    """
    Initialize database tables using models from timetables_etl.

    """
    if db.backend != DatabaseBackend.SQLITE:
        raise ValueError("Postgres is managed by Django and relationships are missing")
    metadata = MetaData()

    model_classes = [
        getattr(models, attr_name)
        for attr_name in models.__all__
        if hasattr(getattr(models, attr_name), "__table__")
    ]
    log.info("Modesl Found", count=len(model_classes))

    for model in model_classes:
        log.debug("Processing Model for Table Creation", model_name=model.__name__)
        columns = [
            Column(
                column.name,
                column.type,
                primary_key=column.primary_key,
                nullable=column.nullable,
                index=column.index,
                unique=column.unique,
            )
            for column in model.__table__.columns
        ]

        Table(model.__table__.name, metadata, *columns, extend_existing=True)
        log.info(
            "Table Created", table_name=model.__table__.name, columns_count=len(columns)
        )

    try:
        metadata.create_all(db.engine)
    except Exception as e:
        raise RuntimeError(f"Failed to create tables: {str(e)}") from e
