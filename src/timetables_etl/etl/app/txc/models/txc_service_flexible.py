"""
TXC Flexible Service Models
"""

from pydantic import BaseModel, Field


class TXCFlexibleStopUsage(BaseModel):
    """
    Flexible Stops
    """

    StopPointRef: str


class TXCFixedStopUsage(BaseModel):
    """
    Fxed Stops
    """

    StopPointRef: str
    TimingStatus: str


class TXCPhone(BaseModel):
    """
    Phone Number
    """

    TelNationalNumber: str


class TXCBookingArrangements(BaseModel):
    """
    Information on how to book Flexible Service
    """

    Description: str
    Phone: TXCPhone | None = None
    Email: str | None = None
    WebAddress: str | None = None
    AllBookingsTaken: bool = False


class TXCFlexibleJourneyPattern(BaseModel):
    """
    Pattern of Journeys Making up the FlexibleService
    """

    id: str
    Direction: str
    StopPointsInSequence: list[TXCFixedStopUsage | TXCFlexibleStopUsage]
    FlexibleZones: list[TXCFlexibleStopUsage] = Field(default=[])
    BookingArrangements: TXCBookingArrangements | None = None


class TXCFlexibleService(BaseModel):
    """
    A service with variable pick-up points and no fixed operational schedule
    TODO: Implement Parser
    """

    Origin: str
    Destination: str
    FlexibleJourneyPattern: list[TXCFlexibleJourneyPattern] = Field(default=[])

    UseAllStopPoints: bool
