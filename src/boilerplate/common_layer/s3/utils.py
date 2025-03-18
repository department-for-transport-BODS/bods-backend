"""
Utility functions related to S3
"""

from common_layer.exceptions import S3FilenameParseFailed


def get_filename_from_object_key(object_key: str) -> str | None:
    """
    Utility function for returning the filename from an S3 object key.
    """
    parts = object_key.split("/")
    if parts and object_key.strip():
        filename = parts[-1]
        return filename
    return None


def get_filename_from_object_key_except(object_key: str) -> str:
    """
    Utility function for returning the filename from an S3 object key.
    """
    filename = get_filename_from_object_key(object_key)
    if filename:
        return filename
    raise S3FilenameParseFailed(object_key=object_key)
