"""
Description: Utility functions for boilerplate
"""

import hashlib
from typing import Union


def sha1sum(content: Union[bytes, bytearray, memoryview]) -> str:
    """
    Takes the sha1 of a string and returns a hex string
    """
    return hashlib.sha1(content).hexdigest()
