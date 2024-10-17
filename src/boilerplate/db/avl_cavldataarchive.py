from common import LambdaEvent
from datetime import datetime, timezone


def get_cavl_db_object(event: LambdaEvent, data_format: str):
    """Get Cavl record from the db given the data_format value

    Args:
        event (LambdaEvent): Event object which contains the db connection details
        data_format (str): value of the dataformat for which record is required

    Returns:
        database record for the object
    """
    cavl_data_archive = event.db.classes.avl_cavldataarchive
    archive = (
        event.db.session.query(cavl_data_archive)
        .where(cavl_data_archive.data_format == data_format)
        .first()
    )
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
    event.db.session.add(record)
    event.db.session.commit()
