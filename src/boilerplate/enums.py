from enum import Enum, unique


@unique
class CAVLDataFormat(Enum):
    SIRIVM = "VM"
    GTFSRT = "RT"
    SIRIVM_TFL = "TL"
