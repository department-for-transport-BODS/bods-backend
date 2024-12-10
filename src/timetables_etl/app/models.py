"""
Pydantic Models 
"""

from pydantic import BaseModel, ConfigDict

from .database.models import (
    DatasetETLTaskResult,
    OrganisationDatasetRevision,
    OrganisationTXCFileAttributes,
    TransmodelService,
    TransmodelServicePattern,
)


class ETLInputData(BaseModel):
    """
    Input data for the ETL Function
    """

    revision_id: int
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


class TransformedData(BaseModel):
    """
    TXC Data transformed into the SQLAlchemy models to be applied on the DB
    """

    transmodel_service: list[TransmodelService]
    transmodel_servicepatterns: list[TransmodelServicePattern]
