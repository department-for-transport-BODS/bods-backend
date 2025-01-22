"""
FileValidation Lambda Pydantic Models and Dataclasses
"""

from pydantic import BaseModel, Field


class FileValidationInputData(BaseModel):
    """
    Input data for the File Validation
    """

    revision_id: int = Field(alias="DatasetRevisionId")
    s3_bucket_name: str = Field(alias="Bucket")
    s3_file_key: str = Field(alias="ObjectKey")
