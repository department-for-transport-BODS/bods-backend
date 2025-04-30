"""
Namespace helpers
"""

from lxml.etree import _Element  # type: ignore


def get_namespaces(xml: _Element) -> dict[str, str]:
    """
    Get Namespace
    """
    default_ns = xml.nsmap.get(None)
    return {"x": default_ns} if default_ns is not None else {}
