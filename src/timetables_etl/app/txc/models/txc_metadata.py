"""
Metadata from a TXC File
"""

from pydantic import BaseModel, Field

from .txc_types import ModificationType


class TXCMetadata(BaseModel):
    """
    Metadata of TXC File
    """

    SchemaVersion: str | None = Field(
        None, description="Version number of the TransXChange schema"
    )
    ModificationDateTime: str | None = Field(
        None, description="Date and time when this instance document was last modified"
    )
    Modification: ModificationType | None = Field(
        None,
        description="Nature of last modification to document.",
    )
    RevisionNumber: str | None = Field(None, description="Version number of document")
    CreationDateTime: str | None = Field(
        None, description="Date and time when this instance document was created"
    )
