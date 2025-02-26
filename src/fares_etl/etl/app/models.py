"""
Pydantic Models 
"""

from pydantic import BaseModel, ConfigDict, Field


class ETLInputData(BaseModel):
    """
    Input data for the ETL Function
    """

    model_config = ConfigDict(populate_by_name=True)

    revision_id: int = Field(alias="DatasetRevisionId")
    s3_bucket_name: str = Field(alias="Bucket")
    s3_file_key: str = Field(alias="ObjectKey")
    metadata_id: int = Field(alias="MetadataId")
