"""
Utils for working with Iterparse
"""

from lxml.etree import _Element  # type: ignore


def unload_element(elem: _Element) -> None:
    """
    Clean up processed element and its ancestors to free memory.
    """
    elem.clear()
    parent = elem.getparent()
    if parent is not None:
        previous = elem.getprevious()
        while previous is not None:
            parent.remove(previous)
            previous = elem.getprevious()
