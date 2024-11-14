import logging
from typing import Optional

logger = logging.getLogger(__name__)


# Exception for Pipeline
class PipelineException(Exception):
    """Basic exception for errors raised by a pipeline"""

    def __init__(self, message: Optional[str] = None):
        if message is None:
            # Set some default error message
            message = "An error occurred in the pipeline"
        super().__init__(message)
