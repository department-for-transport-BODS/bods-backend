from typing import TypedDict

from pydantic import BaseModel, Field


class ResultFile(BaseModel):
    """
    Individual result file from the Map state
    """

    Key: str
    Size: int


class ResultFiles(BaseModel):
    """
    Collection of result files grouped by status
    """

    FAILED: list[ResultFile] = Field(default_factory=list)
    PENDING: list[ResultFile] = Field(default_factory=list)
    SUCCEEDED: list[ResultFile] = Field(default_factory=list)


class MapResults(BaseModel):
    """
    Results from the Map state execution
    """

    DestinationBucket: str
    MapRunArn: str
    ResultFiles: ResultFiles


class GenerateOutputZipInputData(BaseModel):
    """
    Input parameters for the Lambda function
    """

    class Config:
        """Configuration for the model"""

        populate_by_name = True

    map_run_arn: str = Field(alias="MapRunArn")
    destination_bucket: str = Field(alias="DestinationBucket")
    output_prefix: str = Field(alias="OutputPrefix")
    dataset_revision_id: int = Field(alias="DatasetRevisionId")


class ProcessingResult(TypedDict):
    """
    Result of processing the zip operation
    """

    successful_files: int
    failed_files: int
    zip_location: str
