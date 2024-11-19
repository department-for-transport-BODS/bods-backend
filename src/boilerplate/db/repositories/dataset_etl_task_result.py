import logging

from common import BodsDB
from exceptions.pipeline_exceptions import PipelineException
from sqlalchemy.orm.exc import NoResultFound

logger = logging.getLogger(__name__)


class DatasetETLTaskResultRepository:

    def __init__(self, db: BodsDB):
        self._db = db

    def get_by_id(self, id: int):
        try:
            with self._db.session as session:
                task = session.query(self._db.classes.pipelines_datasetetltaskresult).filter_by(id=id).one()
        except NoResultFound as exc:
            message = f"DatasetETLTaskResult {id} does not exist."
            logger.exception(message, exc_info=True)
            raise PipelineException(message) from exc
        else:
            return task

    def update(self, record):
        with self._db.session as session:
            try:
                session.add(record)
                session.commit()
            except Exception as exc:
                session.rollback()
                message = f"Failed to update DatasetETLTaskResult: {exc}"
                logger.error(message)
                raise PipelineException(message) from exc

