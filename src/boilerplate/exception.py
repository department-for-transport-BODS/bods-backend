import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PipelineException(Exception):
    """Basic exception for errors raised by a pipeline"""

    def __init__(self, message: Optional[str] = None, step_name: Optional[str] = ""):
        if message is None:
            # Set some default error message
            message = "An error occurred in the pipeline"

        self.error_info = json.dumps({"error_message": message, "step_name": step_name})

        super().__init__(self.error_info)
