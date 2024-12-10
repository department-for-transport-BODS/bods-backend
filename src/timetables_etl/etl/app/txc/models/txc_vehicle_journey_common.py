"""
Common to Normal Vehicle Journey and Flexible ones
"""

from pydantic import BaseModel, Field


class TXCBlock(BaseModel):
    """
    Block Section
    VehicleJourney -> Operational -> Block
    """

    Description: str = Field(
        ..., description="Description of the block (running board) of the journey"
    )
    BlockNumber: str | None = Field(
        ..., description="Reference number for the Block or Running Board."
    )


class TXCTicketMachine(BaseModel):
    """
    Ticket Machine Section
    VehicleJourney -> Operational -> TicketMachine
    """

    JourneyCode: str | None = Field(
        default=None,
        description="The identifier used by the ticket machine system to refer to the journey.",
    )


class TXCOperational(BaseModel):
    """
    VehicleJourney Operational Section
    """

    TicketMachine: TXCTicketMachine | None = Field(
        default=None, description="associate the journey with ticket machine settings."
    )
    Block: TXCBlock | None = Field(
        default=None,
        description="Data elements used to associate journey with a block (running board).",
    )
