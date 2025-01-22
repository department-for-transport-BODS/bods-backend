"""
Common Enums
"""

from enum import Enum, unique


@unique
class CAVLDataFormat(Enum):
    """
    CAVL Data Format Types
    """

    SIRIVM = "VM"
    GTFSRT = "RT"
    SIRIVM_TFL = "TL"


class FeedStatus(str, Enum):
    """
    Revision Status Field Enum
    """

    PENDING = "pending"
    DRAFT = "draft"
    INDEXING = "indexing"
    LIVE = "live"
    SUCCESS = "success"
    EXPIRING = "expiring"
    WARNING = "warning"
    ERROR = "error"
    EXPIRED = "expired"
    DELETED = "deleted"
    INACTIVE = "inactive"
