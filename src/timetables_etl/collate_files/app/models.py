"""
Collete Files Models
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class CollateFilesInputData(BaseModel):
    """
    Input data for the Collate
    """

    model_config = ConfigDict(populate_by_name=True)

    map_run_arn: str = Field(alias="MapRunArn")
    map_run_prefix: str = Field(alias="MapRunPrefix")
    s3_bucket_name: str = Field(alias="Bucket")
    revision_id: int = Field(alias="DatasetRevisionId")


class ETLMapInputData(BaseModel):
    """
    A PTI / ETL Map input data set
    A list of these are generated as a JSON for the input step
    """

    model_config = ConfigDict(populate_by_name=True)

    s3_bucket_name: Annotated[str, Field(alias="Bucket")]
    s3_file_key: Annotated[str, Field(alias="ObjectKey")]
    superseded_timetable: Annotated[
        bool, Field(alias="SupersededTimetable", default=False)
    ]
    file_attributes_id: Annotated[int, Field(alias="TxcFileAttributesId")]
