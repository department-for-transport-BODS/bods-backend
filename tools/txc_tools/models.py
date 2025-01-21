"""
Model definitions for txc tools
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class XMLFileInfo(BaseModel):
    """Pydantic model for XML file information"""

    model_config = ConfigDict(frozen=True)

    file_path: str = Field(..., description="Path to the XML file within the zip")
    size_mb: Decimal = Field(
        ..., description="Size of the XML file in megabytes", decimal_places=2
    )
    parent_zip: str | None = Field(
        None, description="Name of the parent zip file if nested"
    )


class ZipStats(BaseModel):
    """Pydantic model for zip file statistics"""

    model_config = ConfigDict(frozen=True)

    zip_name: str = Field(..., description="Name of the zip file")
    file_count: int = Field(..., ge=0, description="Number of XML files in the zip")
    total_size_mb: Decimal = Field(
        ..., description="Total size of all XMLs in megabytes", decimal_places=2
    )

    @computed_field
    def avg_file_size_mb(self) -> Decimal:
        """Average size of XML files in the zip"""
        if self.file_count == 0:
            return Decimal("0")
        return (self.total_size_mb / self.file_count).quantize(Decimal("0.01"))


class XMLTagInfo(BaseModel):
    """Pydantic model for XML tag count information"""

    model_config = ConfigDict(frozen=True)

    file_path: str = Field(..., description="Path to the XML file within the zip")
    tag_count: int = Field(
        ..., description="Number of occurrences of the specified tag"
    )
    parent_zip: str | None = Field(
        None, description="Name of the parent zip file if nested"
    )


class ZipTagStats(BaseModel):
    """Pydantic model for zip file tag statistics"""

    model_config = ConfigDict(frozen=True)

    zip_name: str = Field(..., description="Name of the zip file")
    file_count: int = Field(..., ge=0, description="Number of files containing the tag")
    total_tags: int = Field(..., description="Total number of tag occurrences")
