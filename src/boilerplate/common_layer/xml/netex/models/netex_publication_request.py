"""
PublicationRequestStructure Models
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from .netex_publication_request_topics import NetworkFrameTopicStructure
from .netex_utility import MultilingualString


class NetworkFrameRequestPolicyStructure(BaseModel):
    """
    Structure for Network Frame Request Policy

    Not Implemented
    """


class NetworkFrameSubscriptionPolicyStructure(BaseModel):
    """
    Structure for Network Frame Subscription Policy

    Not Implemented
    """


class PublicationRequestStructure(BaseModel):
    """Type for Publication Request."""

    version: Annotated[
        str, Field(default="1.0", description="Version of the publication request")
    ]

    RequestTimestamp: Annotated[datetime | None, Field(description="Time of request.")]

    ParticipantRef: Annotated[
        str | None, Field(default=None, description="Reference to a participant system")
    ]

    Description: Annotated[
        MultilingualString | None,
        Field(default=None, description="Description of the request"),
    ]

    topics: Annotated[
        list[NetworkFrameTopicStructure] | None,
        Field(
            default=None,
            description=(
                "One or more Request filters that specify the data to be included in output."
                "Multiple filters are logically ANDed."
            ),
        ),
    ]

    RequestPolicy: Annotated[
        NetworkFrameRequestPolicyStructure | None,
        Field(
            default=None,
            description="Policies to apply when fetching data specified by Topics.",
        ),
    ]

    SubscriptionPolicy: Annotated[
        NetworkFrameSubscriptionPolicyStructure | None,
        Field(
            default=None,
            description="Policy to use when processing Network Subscriptions.",
        ),
    ]
