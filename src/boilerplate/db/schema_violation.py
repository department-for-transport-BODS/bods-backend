from common import BodsDB

from logger import logger
from sqlalchemy.exc import SQLAlchemyError


def get_schema_violation_obj(db, **kwargs):
    return db.classes.data_quality_schemaviolation(
        revision_id=kwargs.get("revision_id"),
        filename=kwargs.get("filename"),
        line=kwargs.get("line"),
        details=kwargs.get("details"),
    )


class SchemaViolation:
    def __init__(self, db: BodsDB):
        self._db = db

    def create(self, violations):
        with self._db.session as session:
            for violation in violations:
                try:
                    violation_obj = get_schema_violation_obj(self._db,
                                                             **violation)
                    session.add(violation_obj)
                    session.commit()
                except SQLAlchemyError as err:
                    session.rollback()
                    logger.error(f" Failed to add record {err}", exc_info=True)
                    raise err
        return True
