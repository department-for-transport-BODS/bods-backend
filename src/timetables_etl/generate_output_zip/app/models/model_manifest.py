"""
Models for StateMachine ResultWriter manifest.json
"""

from pydantic import BaseModel, Field


class ManifestResultFile(BaseModel):
    """
    Individual result file information
    The Docs State that there will generally be one file unless it exceeds 5GB
    """

    Key: str = Field(min_length=1)
    Size: int = Field(gt=0)


class ManifestResultFilesStatus(BaseModel):
    """
    Structure containing lists of result files by status
    """

    FAILED: list[ManifestResultFile]
    PENDING: list[ManifestResultFile]
    SUCCEEDED: list[ManifestResultFile]


class MapResultManifest(BaseModel):
    """
    AWS Statemachine Manifest.json file structure
    Outputted to S3 when ResultWriter is configured on a Map
    """

    DestinationBucket: str = Field(min_length=1)
    MapRunArn: str = Field(pattern=r"^arn:aws:states:.*")
    ResultFiles: ManifestResultFilesStatus
