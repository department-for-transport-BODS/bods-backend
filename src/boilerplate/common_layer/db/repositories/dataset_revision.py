import logging

from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo,
)
from common_layer.db import BodsDB, DbManager
from common_layer.exceptions.pipeline_exceptions import PipelineException
from sqlalchemy.exc import NoResultFound

logger = logging.getLogger(__name__)


def get_revision(db, dataset_revision_id):
    """
    Retrieves the revision corresponding to the given dataset ETL task result.
    """
    revision_repo = OrganisationDatasetRevisionRepo(db)
    return revision_repo.get_by_id(dataset_revision_id)


def update_file_hash_in_db(
    file_name, revision_id, original_file_hash=None, modified_file_hash=None
):
    """
    Update modified hash to db
    """
    if original_file_hash is None and modified_file_hash is None:
        logger.warning(f"Nothing to update for {file_name}")
        return None

    logger.info(f"Updating the hash of {file_name} to db")
    dataset_revision = DatasetRevisionRepository(DbManager.get_db())
    revision = dataset_revision.get_by_id(revision_id)
    if original_file_hash:
        revision.original_file_hash = original_file_hash
    if modified_file_hash:
        revision.modified_file_hash = modified_file_hash
    dataset_revision.update(revision)


class DatasetRevisionRepository:

    def __init__(self, db: BodsDB):
        self._db = db

    def get_by_id(self, id: int):
        try:
            with self._db.session as session:
                result = (
                    session.query(self._db.classes.organisation_datasetrevision)
                    .filter_by(id=id)
                    .one()
                )
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
