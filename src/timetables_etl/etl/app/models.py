"""
Pydantic Models 
"""

from pydantic import BaseModel, ConfigDict

from .database.models import (
    DatasetETLTaskResult,
    OrganisationDatasetRevision,
    OrganisationTXCFileAttributes,
)


class ETLInputData(BaseModel):
    """
    Input data for the ETL Function
    """

    task_id: int
    file_attributes_id: int
    s3_bucket_name: str
    s3_file_key: str


class TaskData(BaseModel):
    """
    Task information to be passed around
    """

    model_config = ConfigDict(frozen=True)

    etl_task: DatasetETLTaskResult
    revision: OrganisationDatasetRevision
    file_attributes: OrganisationTXCFileAttributes
    input_data: ETLInputData
