"""
Models Related to Processing the Zip Output
"""

from pydantic import BaseModel


class ProcessingResult(BaseModel):
    """
    Result of processing the zip operation
    """

    successful_files: int
    failed_files: int
    output_location: str
    file_hash: str
