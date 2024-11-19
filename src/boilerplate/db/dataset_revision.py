import time
from common import BodsDB
from logger import logger
from exceptions.db_exceptions import NoRowFound


def get_dataset_revision(db: BodsDB, revision_id: int):
    """Get Organisation revison record from the db given the revision id value

    Args:
        db: BODs DB instance
        revision_id (int): value of the revision id for which record is required

    Returns:
        archive: database record for the object
    """
    if not db.session:
        raise ValueError("No database session provided")

    dataset_revision = db.classes.organisation_datasetrevision
    with db.session as session:
        start_query_op = time.time()
        dataset_revision_obj = (
            session.query(dataset_revision)
            .where(dataset_revision.id == revision_id)
            .first()
        )
        end_query_op = time.time()
        logger.info(f"Query execution time: {end_query_op-start_query_op:.2f} seconds")
        if dataset_revision_obj is None:
            raise NoRowFound(field_name="revision_id", field_value=revision_id)
        return dataset_revision_obj
