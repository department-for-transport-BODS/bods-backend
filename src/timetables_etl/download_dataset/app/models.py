"""
DownloadData Pydantic Models and Dataclasses
"""

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Literal, TypeAlias

from pydantic import AnyUrl, BaseModel, ConfigDict, Field

FileType: TypeAlias = Literal["zip", "xml"]


class ContentType(Enum):
    """Supported content types for downloads."""

    ZIP = auto()
    XML = auto()
    UNKNOWN = auto()


class DownloadDatasetInputData(BaseModel):
    """
    Input data for the download dataset function
    """

    model_config = ConfigDict(populate_by_name=True)

    s3_bucket_name: str = Field(alias="Bucket")
    remote_dataset_url_link: AnyUrl = Field(alias="url")
    revision_id: int = Field(alias="DatasetRevisionId")


@dataclass
class DownloadResult:
    """Result of a file download operation."""

    path: Path
    filetype: FileType
    size: int
