import logging
from boilerplate.common import BodsDB
from boilerplate.exception import PipelineException
from sqlalchemy.orm.exc import NoResultFound

logger = logging.getLogger(__name__)


class DatasetETLTaskResultRepository:

    @staticmethod
    def get_by_id(id: int):
        try:
            db = BodsDB()
            with db.session as session:
                task = session.query(db.classes.pipelines_datasetetltaskresult).filter_by(id=id).one()
        except NoResultFound as exc:
            message = f"DatasetETLTaskResult {id} does not exist."
            logger.exception(message, exc_info=True)
            raise PipelineException(message) from exc
        else:
            return task

    @staticmethod
    def update(record):
        raise NotImplementedError("TODO")
