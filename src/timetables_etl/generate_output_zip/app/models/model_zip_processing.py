"""
Models Related to Processing the Zip Output
"""

from typing import TypedDict


class ProcessingResult(TypedDict):
    """
    Result of processing the zip operation
    """

    successful_files: int
    failed_files: int
    zip_location: str
