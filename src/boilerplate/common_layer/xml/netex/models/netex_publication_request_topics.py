"""
PublicationDelivery -> PublicationRequest -> topics
"""

from typing import Annotated

from common_layer.xml.netex.models.netex_references import ObjectReferences
from pydantic import BaseModel, Field

from .netex_selection_validity import SelectionValidityConditions
from .netex_utility import VersionedRef


class NetworkFilterByValueStructure(BaseModel):
    """Structure for network filter by value"""

    objectReferences: Annotated[
        ObjectReferences, Field(description="References to objects to filter by")
    ]


class NetworkFrameTopicStructure(BaseModel):
    """Type for a Data Object Filter Topic."""

    selectionValidityConditions: Annotated[
        list[SelectionValidityConditions],
        Field(
            description="Validity conditions to apply when selecting data. Applies to frame."
        ),
    ]
    TypeOfFrameRef: Annotated[VersionedRef | None, Field(description="")]
    NetworkFilterByValue: Annotated[
        list[NetworkFilterByValueStructure],
        Field(description="filter by reference value, rather than frame"),
    ]
