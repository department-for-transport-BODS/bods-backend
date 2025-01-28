"""
Stop Point Availability
"""

from datetime import date

from pydantic import BaseModel, Field


class DateRangeStructure(BaseModel):
    """Date range with start and optional end date."""

    StartDate: date = Field(..., description="Start date of the date range")
    EndDate: date | None = Field(
        default=None,
        description=(
            "End date of the date range. If omitted, the range end is open-ended"
        ),
    )


class StopValidityStructure(BaseModel):
    """Validity period and status of a stop."""

    DateRange: DateRangeStructure = Field(
        ...,
        description=(
            "Validity period for which Active/Suspended or Transferred status applies. "
            "Each StartDate closes any previous open-ended date range of a previous "
            "validity element"
        ),
    )
    Active: bool | None = Field(
        default=None,
        description="Stop is active during the period defined by date range",
    )
    Suspended: bool | None = Field(
        default=None,
        description="Stop is suspended during the period specified by date range",
    )
    Transferred: str | None = Field(
        default=None,
        description=(
            "Stop is suspended during period specified by date range, and use is "
            "transferred to the indicated stop. Transference should not be cyclic"
        ),
    )
    Note: str | None = Field(
        default=None,
        description=(
            "Note explaining any reason for activation, transfer or suspension"
        ),
    )


class StopAvailabilityStructure(BaseModel):
    """Availability of a stop for use."""

    StopValidity: list[StopValidityStructure] = Field(
        ...,
        description=(
            "Description of periods for stop activity. Stop validity elements should "
            "be listed in historical order of Date Range Start date"
        ),
    )
