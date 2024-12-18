"""
Pydantic Models 
"""

from common_layer.database.models import (
    DatasetETLTaskResult,
    OrganisationDatasetRevision,
    OrganisationTXCFileAttributes,
)
from pydantic import BaseModel, ConfigDict, Field


class ETLInputData(BaseModel):
    """
    Input data for the ETL Function
    """

    class Config:
        """
        Allow us to map Bucket / Object Key
        """

        allow_population_by_field_name = True

    task_id: int = Field(alias="DatasetEtlTaskResultId")
    file_attributes_id: int = Field(alias="fileAttributesId")
    s3_bucket_name: str = Field(alias="Bucket")
    s3_file_key: str = Field(alias="ObjectKey")


class TaskData(BaseModel):
    """
    Task information to be passed around
    """

    model_config = ConfigDict(frozen=True)

    etl_task: DatasetETLTaskResult
    revision: OrganisationDatasetRevision
    file_attributes: OrganisationTXCFileAttributes
    input_data: ETLInputData
