"""
A set of NeTEx objects as assembled by a publication request or other service. 
Provides a general purpose wrapper for NeTEx data content.
"""

from datetime import datetime, timedelta
from typing import Annotated

from pydantic import BaseModel, Field

from .data_objects import CompositeFrame, ResourceFrame, ServiceFrame
from .fare_frame import FareFrame
from .netex_publication_request import PublicationRequestStructure
from .netex_utility import MultilingualString


class PublicationDeliveryStructure(BaseModel):
    """A set of NeTEx objects as assembled by a publication request or other service.
    Provides a general purpose wrapper for NeTEx data content."""

    # Attributes
    version: Annotated[
        str, Field(default="1.0", description="Type for Publication Delivery")
    ] = "1.0"
    # Children
    PublicationTimestamp: Annotated[
        datetime, Field(description="Time of output of data.")
    ]

    ParticipantRef: Annotated[
        str, Field(description="Reference to a participant system")
    ]

    PublicationRequest: Annotated[
        PublicationRequestStructure | None,
        Field(default=None, description="Echo Request used to create bulk response."),
    ]

    PublicationRefreshInterval: Annotated[
        timedelta | None,
        Field(default=None, description="How often data in publication is refreshed."),
    ]

    Description: Annotated[
        MultilingualString | None,
        Field(default=None, description="Description of contents."),
    ]
    dataObjects: Annotated[
        list[CompositeFrame | ResourceFrame | ServiceFrame | FareFrame],
        Field(default=None, description="Frames"),
    ]
