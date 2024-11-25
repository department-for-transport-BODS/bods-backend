import logging
from common import BodsDB
from db.repositories.dataset_etl_task_result import (
    DatasetETLTaskResultRepository
)
from exceptions.pipeline_exceptions import PipelineException
from sqlalchemy.orm.exc import NoResultFound

logger = logging.getLogger(__name__)


def get_revision(db, dataset_revision_id):
    """
    Retrieves the revision corresponding to the given dataset ETL task result.
    """
    revision_repo = DatasetRevisionRepository(db)
    return revision_repo.get_by_id(dataset_revision_id)


class DatasetRevisionRepository:

    def __init__(self, db: BodsDB):
        self._db = db

    def get_by_id(self, id: int):
        try:
            with self._db.session as session:
                result = session.query(
                    self._db.classes.organisation_datasetrevision).\
                    filter_by(id=id).one()
        except NoResultFound as exc:
            message = f"DatasetRevision {id} does not exist."
            logger.exception(message, exc_info=True)
            raise PipelineException(message) from exc
        else:
            return result

    def update(self, record):
        with self._db.session as session:
            try:
                session.add(record)
                session.commit()
            except Exception as exc:
                session.rollback()
                message = f"Failed to update DatasetRevision: {exc}"
                logger.error(message)
                raise PipelineException(message) from exc
