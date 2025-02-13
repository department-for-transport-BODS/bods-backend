"""
Netex Utility Structures
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class MultilingualString(BaseModel):
    """Type for a string in a specified language."""

    value: Annotated[
        str,
        Field(description="The text value"),
    ]

    lang: Annotated[
        str | None, Field(default=None, description="Language of string contents.")
    ] = None

    textIdType: Annotated[
        str | None, Field(default=None, description="Resource id of string.")
    ] = None


class FromToDate(BaseModel):
    """
    A FromDate and ToDate Structure
    """

    FromDate: Annotated[datetime | None, Field(description="Start Date")]
    ToDate: Annotated[datetime | None, Field(description="End Date")]


class VersionedRef(BaseModel):
    """Base class for versioned references"""

    version: Annotated[str, Field(description="Version of the reference")]
    ref: Annotated[str, Field(description="Reference value")]
