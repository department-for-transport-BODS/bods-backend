import logging
from typing import Optional
from sqlalchemy.orm.exc import NoResultFound

from common import BodsDB

db = BodsDB()

logger = logging.getLogger(__name__)


class PipelineException(Exception):
    """Basic exception for errors raised by a pipeline"""

    def __init__(self, message: Optional[str] = None):
        if message is None:
            # Set some default error message
            message = "An error occurred in the pipeline"
        super().__init__(message)
