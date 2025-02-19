"""
Selection Validity Conditions
"""

from typing import Annotated

from pydantic import BaseModel, Field

from .netex_utility import FromToDate


class AvailabilityCondition(FromToDate):
    """Container for validity conditions"""

    # Attributes
    version: Annotated[str, Field(description="Version of the publication request")]

    id: Annotated[str, Field(description="Version of the publication request")]


class SimpleAvailabilityCondition(FromToDate):
    """
    Container for validity conditions

    NetworkFrameTopic -> selectionValidityConditions->SimpleAvailabilityCondition
    """

    # Attributes
    version: Annotated[str, Field(description="Version of the publication request")]

    id: Annotated[str, Field(description="Version of the publication request")]


class SelectionValidityConditions(BaseModel):
    """
    selectionValidityConditions
    """

    AvailabilityConditions: list[AvailabilityCondition] = []
    SimpleAvailabilityConditions: list[SimpleAvailabilityCondition]
