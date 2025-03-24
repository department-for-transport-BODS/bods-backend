"""
Utility functions related to S3
"""

import urllib.parse

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


def format_s3_tags(tags: dict[str, str] | None = None) -> str | None:
    """
    Format dictionary of tags into the URL-encoded string format required by S3
    Returns:
        URL-encoded string of tags in format "key1=value1&key2=value2" or None if no tags
    """
    if not tags:
        return None

    tag_list = [
        f"{urllib.parse.quote(k)}={urllib.parse.quote(v)}" for k, v in tags.items()
    ]

    return "&".join(tag_list)
