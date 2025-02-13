"""
PublicationDelivery -> dataObjects
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ..models import CompositeFrame

log = get_logger()


def parse_data_objects(elem: _Element) -> list[CompositeFrame]:
    """
    Parse dataObjects
    """
    return []
