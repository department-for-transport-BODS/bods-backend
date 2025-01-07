"""
Map Result data from S3 Models
"""

from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel


class MapRunStatus(str, Enum):
    """Status of map run executions"""

    FAILED = "FAILED"
    RUNNING = "RUNNING"
    ABORTED = "ABORTED"
    SUCCEEDED = "SUCCEEDED"


class MapResultBucket(BaseModel):
    """Bucket information"""

    model_config = ConfigDict(frozen=True)

    name: str


class MapResultObject(BaseModel):
    """Object information"""

    model_config = ConfigDict(frozen=True)

    key: str


class MapResultManifestDetail(BaseModel):
    """Input detail structure from the manifest"""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    bucket: MapResultBucket
    object: MapResultObject
    datasetRevisionId: Annotated[str, Field(min_length=1)]
    datasetType: Annotated[str, Field(min_length=1)]


class MapResultManifestInput(BaseModel):
    """Input structure from the manifest"""

    model_config = ConfigDict(frozen=True)

    Bucket: Annotated[str, Field(min_length=1)]
    DatasetRevisionId: Annotated[str, Field(min_length=1)]
    detail: MapResultManifestDetail
    DatasetEtlTaskResultId: Annotated[int, Field(gt=0)]
    Key: Annotated[str, Field(min_length=1)]


class MapResultManifest(BaseModel):
    """Single entry in the manifest.json"""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True, strict=True)

    Cause: str
    Error: str
    ExecutionArn: Annotated[str, Field(pattern=r"^arn:aws:states:.*")]
    Input: MapResultManifestInput
    InputDetails: dict[str, bool]
    Name: Annotated[str, Field(min_length=1)]
    OutputDetails: dict[str, bool]
    RedriveCount: Annotated[int, Field(ge=0)]
    RedriveStatus: Annotated[str, Field(min_length=1)]
    StartDate: datetime
    StateMachineArn: Annotated[str, Field(pattern=r"^arn:aws:states:.*")]
    Status: MapRunStatus
    StopDate: datetime


class MapResultFailed(RootModel):
    """Root model for FAILED_n.json files"""

    root: list[MapResultManifest]


class MapResultSucceeded(RootModel):
    """Root model for SUCCEEDED_n.json files"""

    root: list[MapResultManifest]


class MapResultPending(RootModel):
    """Root model for PENDING_n.json files"""

    root: list[MapResultManifest]
