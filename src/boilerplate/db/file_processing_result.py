"""
Description: Module contains the database functionality for
             FileProcessingResult table
"""

from typing import Callable
from sqlalchemy.exc import SQLAlchemyError
from common import BodsDB
from logger import logger
from models import FileProcessingResult


def _execute(operation: Callable):
    """
    Executes the given operation
    :param operation: Callable operation
    :return: None if the operation was successful,
             otherwise an exception
    """
    _session = BodsDB.session
    try:
        result = operation(_session)
        _session.commit()
        return result
    except SQLAlchemyError as err:
        _session.rollback()
        logger.error(err)
        raise err
    finally:
        _session.close()


def create(file_processing_result: FileProcessingResult):
    """
    Creates a new FileProcessingResult instance
    :param file_processing_result: FileProcessingResult data
    :return: None if the operation was successful,
             otherwise an exception
    """

    def operation(session):
        session.add(file_processing_result)
        return "File processing entity created successfully!"

    return _execute(operation)


def get(revision_id):
    """
    Get file processing result by revision ID
    :param revision_id: int
    :return: return file processing result by revision ID
             or None if no file processing result was found
    """

    def operation(session):
        return (
            session.query(FileProcessingResult)
            .filter(FileProcessingResult.revision == revision_id)
            .first()
        )

    return _execute(operation)


def update(revision_id, file_processing_result):
    """
    Update file processing result by revision ID
    :param revision_id: int
    :param file_processing_result: FileProcessingResult data
    :return:
    """

    def operation(session):
        result = (
            session.query(FileProcessingResult)
            .filter(FileProcessingResult.revision == revision_id)
            .first()
        )
        # Update
        result.filename = file_processing_result.filename

    return _execute(operation)
