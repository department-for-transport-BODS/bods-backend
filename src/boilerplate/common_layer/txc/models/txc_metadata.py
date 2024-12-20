"""
Metadata from a TXC File
"""

from datetime import datetime

from pydantic import BaseModel, Field

from .txc_types import ModificationType


class TXCMetadata(BaseModel):
    """
    Metadata of TXC File
    """

    SchemaVersion: str = Field(
        ..., description="Version number of the TransXChange schema"
    )
    ModificationDateTime: datetime = Field(
        ..., description="Date and time when this instance document was last modified"
    )
    Modification: ModificationType = Field(
        ...,
        description="Nature of last modification to document.",
    )
    RevisionNumber: int = Field(..., description="Version number of document")
    CreationDateTime: datetime = Field(
        ..., description="Date and time when this instance document was created"
    )
    FileName: str = Field(
        ..., description="The File Name defined in the header of the xml"
    )
    RegistrationDocument: bool | None = Field(
        default=None, description="Whether this is a registration document"
    )
    FileHash: str | None = Field(
        default=None,
        description="File Hash that needs to be calucated out of the parsed data",
    )
