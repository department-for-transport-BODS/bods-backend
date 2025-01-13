"""
Lambda Specific Models
"""

from pydantic import BaseModel, Field


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
