import time
from common import LambdaEvent
from datetime import datetime, timezone
from logger import logger


def get_cavl_db_object(event: LambdaEvent, data_format: str):
    """Get Cavl record from the db given the data_format value

    Args:
        event (LambdaEvent): Event object which contains the db connection details
        data_format (str): value of the dataformat for which record is required

    Returns:
        archive: database record for the object
    """
    cavl_data_archive = event.db.classes.avl_cavldataarchive

    with event.db.session as session:
        start_query_op = time.time()
        archive = (
            session.query(cavl_data_archive)
            .where(cavl_data_archive.data_format == data_format)
            .first()
        )
        end_query_op = time.time()
        logger.info(f"Query execution time: {end_query_op-start_query_op:.2f} seconds")    
        if archive is None:
            archive = cavl_data_archive(
                data_format=data_format,
                created=datetime.now(timezone.utc),
                last_updated=datetime.now(timezone.utc),
            )
        return archive


def update_cavl_db_object(event: LambdaEvent, filename: str, data_format: str):
    """Search and update the cavl object in the database

    Args:
        event (LambdaEvent): Lambda event object contains db connection
        filename (str): File name to be saved
        data_format (str): type of dataformat being updated
    """
    archive = get_cavl_db_object(event, data_format)
    archive.data = filename
    archive.last_updated = datetime.now(timezone.utc)

    update_record_in_db(archive, event)


def update_record_in_db(record, event: LambdaEvent):
    """Execute session add and session commit

    Args:
        record : Database record object to be updated
        event (LambdaEvent): Lambda event object contains database connection.
    """
    with event.db.session as session:
        try:
            session.add(record)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update record: {e}")
            raise
