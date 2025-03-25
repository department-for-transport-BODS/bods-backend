"""
S3 Module
"""

from .client import S3
from .upload import (
    ProcessingStats,
    process_file_to_s3,
    process_zip_to_s3,
    process_zip_to_s3_async,
)
from .utils import get_filename_from_object_key_except

__all__ = [
    "S3",
    "process_file_to_s3",
    "process_zip_to_s3",
    "process_zip_to_s3_async",
    "ProcessingStats",
    "get_filename_from_object_key_except",
]
