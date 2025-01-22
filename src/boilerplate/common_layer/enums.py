from enum import Enum, unique


@unique
class CAVLDataFormat(Enum):
    SIRIVM = "VM"
    GTFSRT = "RT"
    SIRIVM_TFL = "TL"


class FeedStatus(str, Enum):
    pending = "pending"
    draft = "draft"
    indexing = "indexing"
    live = "live"
    success = "success"
    expiring = "expiring"
    warning = "warning"
    error = "error"
    expired = "expired"
    deleted = "deleted"
    inactive = "inactive"
