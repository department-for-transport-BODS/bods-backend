"""
Collete Files Models
"""

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

    bucket: str
    object: str
    superceded_file: bool
    fileAttributesEtl: int
