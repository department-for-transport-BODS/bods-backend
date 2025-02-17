"""
Dataclasses for Stop Points
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class NonExistentNaptanStop:
    """
    Used when operators define an AnnotatedStopPointRef for a stop point
    that doesn't exist in Naptan
    """

    atco_code: str
    common_name: str
