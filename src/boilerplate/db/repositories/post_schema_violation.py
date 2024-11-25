from common import BodsDB
from logger import logger
from sqlalchemy.exc import SQLAlchemyError


def get_post_schema_check_obj(db, **kwargs):
    return db.classes.data_quality_postschemaviolation(
        revision_id=kwargs.get("revision_id"),
        filename=kwargs.get("filename"),
        details=kwargs.get("details")
    )


class PostSchemaViolationRepository:
    def __init__(self, db):
        self._db: BodsDB = db
        
    def create(self, violations):
        with self._db.session as session:
            for violation in violations:
                try:
                    violation_obj = get_post_schema_check_obj(self._db,
                                                              **violation
                                                              )
                    session.add(violation_obj)
                    session.commit()
                except SQLAlchemyError as err:
                    session.rollback()
                    logger.error(f" Failed to add record {err}", exc_info=True)
                    raise err
        return True
