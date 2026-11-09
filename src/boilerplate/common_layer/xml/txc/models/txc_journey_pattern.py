"""

TXC Journey Patterns
"""

from pydantic import BaseModel, Field, field_validator

from .txc_types import ActivityT, TimingStatusT
from .txc_validators import convert_runtime


class TXCJourneyPatternStopUsage(BaseModel):
    """
    The From or To section of a JourneyPatternTimingLink
    """

    id: str
    SequenceNumber: str | None = Field(
        default=None, description="Attribute: Stop Sequence"
    )
    WaitTime: str | None = Field(
        default=None, description="The total wait time at the stop."
    )
    Activity: ActivityT = Field(
        ...,
        description="The activity at the stop, such as pickup, setDown, pickUpAndSetDown, or pass.",
    )
    DynamicDestinationDisplay: str | None = Field(
        default=None,
        description="Description of the destination at this stop, useful for circular services.",
    )
    Notes: str | None = Field(
        default=None,
        description="Additional notes that may be included where appropriate.",
    )
    StopPointRef: str = Field(
        ...,
        description="The AtcoCode or pseudo-AtcoCode of the stop point.",
    )
    TimingStatus: TimingStatusT | None = Field(
        default=None,
        description=(
            "Timing Reliability at the stop."
            "TXC-PTI uses words instead of 3 letter codes"
        ),
    )
    FareStageNumber: int | None = Field(
        default=None,
        description="The fare stage number for this stop.",
    )
    FareStage: bool | None = Field(
        default=None,
        description="A flag indicating if a fare stage is changing at this stop.",
    )


class TXCJourneyPatternTimingLink(BaseModel):
    """
    describes a timed link connecting two stops of a JourneyPattern of a StandardService
    """

    id: str = Field(..., description="Unique identifie link.")
    From: TXCJourneyPatternStopUsage = Field(
        ..., alias="From", description="The departure stop and activity."
    )
    To: TXCJourneyPatternStopUsage = Field(
        ..., alias="To", description="The arrival stop and activity."
    )
    RouteLinkRef: str = Field(..., description="Reference to a defined route link.")
    RunTime: str = Field(
        ...,
        description="Scheduled running time between 'From' and 'To' stops.",
    )
    Distance: str | None = Field(
        default=None,
        description="Distance covered in this segment of the journey pattern, optional.",
    )

    _convert_runtime = field_validator("RunTime")(convert_runtime)


class TXCJourneyPatternSection(BaseModel):
    """
    Groups of JourneyPatternTimingLink with an ID
    """

    id: str = Field(..., description="Unique identifie link.")
    JourneyPatternTimingLink: list[TXCJourneyPatternTimingLink] = Field(
        ...,
        description=(
            "Describes a timed link"
            "connecting two stops of a JourneyPattern of a StandardService"
        ),
    )
