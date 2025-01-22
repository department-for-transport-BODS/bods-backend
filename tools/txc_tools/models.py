"""
Model definitions for txc tools
"""

import queue
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, computed_field


class XMLFileInfo(BaseModel):
    """Pydantic model for XML file information"""

    model_config = ConfigDict(frozen=True)
    file_path: str = Field(
        ..., title="File Path", description="Path to the XML file within the zip"
    )
    size_mb: Decimal = Field(
        ...,
        title="Size (MB)",
        description="Size of the XML file in megabytes",
        decimal_places=2,
    )
    parent_zip: str | None = Field(
        None, title="Parent Zip", description="Name of the parent zip file if nested"
    )


class XMLTagInfo(BaseModel):
    """Pydantic model for XML tag count information"""

    model_config = ConfigDict(frozen=True)

    file_path: str = Field(
        ..., title="File Path", description="Path to the XML file within the zip"
    )
    tag_count: int = Field(
        ..., title="Tag Count", description="Number of occurrences of the specified tag"
    )
    parent_zip: str | None = Field(
        None, title="Parent Zip", description="Name of the parent zip file if nested"
    )


class ZipStats(BaseModel):
    """Pydantic model for zip file statistics"""

    model_config = ConfigDict(frozen=True)

    zip_name: str = Field(..., title="Zip Names", description="Name of the zip file")
    file_count: int = Field(
        ...,
        title="Number of Files in Zip",
        ge=0,
        description="Number of XML files in the zip",
    )
    total_size_mb: Decimal = Field(
        ...,
        title="Total Size of XMLs in Zip (MB)",
        description="Total size of all XMLs in megabytes",
        decimal_places=2,
    )

    @computed_field(
        return_type=Decimal, alias="avg_file_size_mb", title="Average File Size (MB)"
    )
    def avg_file_size_mb(self) -> Decimal:
        """Average size of XML files in the zip"""
        if self.file_count == 0:
            return Decimal("0")
        return (self.total_size_mb / self.file_count).quantize(Decimal("0.01"))


class ZipTagStats(BaseModel):
    """Pydantic model for zip file tag statistics"""

    model_config = ConfigDict(frozen=True)

    zip_name: str = Field(..., title="Zip Names", description="Name of the zip file")
    file_count: int = Field(
        ...,
        ge=0,
        title="Number of Files with Tag",
        description="Number of files containing the tag",
    )
    total_tags: int = Field(
        ...,
        title="Total Tag Occurrences",
        description="Total number of tag occurrences",
    )


class AnalysisMode(str, Enum):
    """Type of file processing"""

    SIZE = "size"
    TAG = "tag"


@dataclass
class WorkerConfig:
    """
    Worker configuration
    """

    zip_ref: zipfile.ZipFile
    file_list: list[zipfile.ZipInfo]
    xml_queue: queue.Queue
    future_queue: queue.Queue
    executor: ThreadPoolExecutor
    mode: AnalysisMode
    tag_name: str | None = None
