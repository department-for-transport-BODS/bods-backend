"""
Enums that constrain what can be placed in fields in the database
"""

from enum import Enum, IntEnum


class ChoiceEnum(Enum):
    """
    Enum with method to return different choices
    """

    @classmethod
    def choices(cls):
        """
        Returns the choices in a suitable way for validation
        """
        return sorted([(key.value, key.name) for key in cls], key=lambda c: c[0])


class DatasetType(IntEnum):
    """
    The types of dataset that bods can ingest
    """

    TIMETABLE = 1
    AVL = 2
    FARES = 3
    DISRUPTIONS = 4

    @classmethod
    def choices(cls) -> list[tuple[int, str]]:
        """Get choices for forms/validation"""
        return [(member.value, member.name) for member in cls]


class AVLFeedStatus(ChoiceEnum):
    """
    AVL feed status
    """

    LIVE = "FEED_UP"
    INACTIVE = "FEED_DOWN"
    ERROR = "SYSTEM_ERROR"
