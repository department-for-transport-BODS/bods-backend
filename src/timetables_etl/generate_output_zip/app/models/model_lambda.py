"""
Lambda Specific Models
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GenerateOutputZipInputData(BaseModel):
    """
    Input parameters for the GenerateOutputZip Lambda
    """

    model_config = ConfigDict(populate_by_name=True)

    map_run_arn: str = Field(alias="MapRunArn")
    map_run_prefix: str = Field(alias="MapRunPrefix")
    destination_bucket: str = Field(alias="DestinationBucket")
    output_prefix: str = Field(alias="OutputPrefix")
    original_object_key: str = Field(alias="OriginalObjectKey")
    dataset_revision_id: int = Field(alias="DatasetRevisionId")
    dataset_etl_task_result_id: int = Field(alias="DatasetEtlTaskResultId")
    publish_dataset_revision: bool = Field(alias="PublishDatasetRevision")
    overwrite_input_dataset: bool = Field(alias="OverwriteInputDataset")
    dataset_type: Literal["timetables", "fares"] = Field(alias="DatasetType")
