"""
PostSchemaCheck Pydantic Models and Dataclasses
"""

from typing import List

from pydantic import BaseModel, ConfigDict, Field


class PostSchemaCheckInputData(BaseModel):
    """
    Input data for the Post Schema Check
    """

    model_config = ConfigDict(populate_by_name=True)

    revision_id: int = Field(alias="DatasetRevisionId")
    s3_bucket_name: str = Field(alias="Bucket")
    s3_file_key: str = Field(alias="ObjectKey")


class PublishedDatasetModel(BaseModel):
    """
    Additional details for published dataset
    """

    published_dataset: int
    service_codes: List[str]


class ValidationResult(BaseModel):
    """
    Result of a validation check with details
    """

    is_valid: bool
    error_code: str | None = None
    additional_details: PublishedDatasetModel | None = None
    message: str | None = None
