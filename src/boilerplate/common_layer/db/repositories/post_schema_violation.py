from common_layer.db import BodsDB
from sqlalchemy.exc import SQLAlchemyError
from structlog.stdlib import get_logger

log = get_logger()


def get_post_schema_check_obj(db, **kwargs):
    return db.classes.data_quality_postschemaviolation(
        revision_id=kwargs.get("revision_id"),
        filename=kwargs.get("filename"),
        details=kwargs.get("details"),
    )


class PostSchemaViolationRepository:
    def __init__(self, db):
        self._db: BodsDB = db

    def create(self, violations):
        with self._db.session as session:
            for violation in violations:
                try:
                    violation_obj = get_post_schema_check_obj(self._db, **violation)
                    session.add(violation_obj)
                    session.commit()
                except SQLAlchemyError as err:
                    session.rollback()
                    log.error("Failed to add record", exc_info=True)
                    raise err
        return True
