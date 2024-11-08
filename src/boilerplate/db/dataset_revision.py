import time
from common import LambdaEvent
from logger import logger
from bods_exception import NoDataFoundError


def get_dataset_revision(event: LambdaEvent, revision_id: int):
    """Get Cavl record from the db given the data_format value

    Args:
        event (LambdaEvent): Event object which contains the db connection details
        data_format (str): value of the dataformat for which record is required

    Returns:
        archive: database record for the object
    """
    dataset_revision = event.db.classes.organisation_datasetrevision

    with event.db.session as session:
        start_query_op = time.time()
        dataset_revision_obj = (
            session.query(dataset_revision)
            .where(dataset_revision.id == revision_id)
            .first()
        )
        end_query_op = time.time()
        logger.info(f"Query execution time: {end_query_op-start_query_op:.2f} seconds")
        if dataset_revision_obj is None:
            raise NoDataFoundError(field_name="revision_id", field_value=revision_id)
        return dataset_revision_obj
