import logging
from exception import PipelineException
from sqlalchemy.orm.exc import NoResultFound

logger = logging.getLogger(__name__)


class DatasetRevisionRepository:

    def __init__(self, db):
        self._db = db

    def get_by_id(self, id: int):
        try:
            with self._db.session as session:
                result = session.query(self._db.classes.organisation_datasetrevision).filter_by(id=id).one()
        except NoResultFound as exc:
            message = f"DatasetETLTaskResult {id} does not exist."
            logger.exception(message, exc_info=True)
            raise PipelineException(message) from exc
        else:
            return result
