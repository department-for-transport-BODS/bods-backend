"""
Model definition for state runner
"""

from pydantic import BaseModel


class StateMachineInputS3Object(BaseModel):
    """
    Class to hold information about S3 object key.
    """

    object: str


class StateMachineS3Payload(BaseModel):
    """
    Class to hold information about state machine payload data from S3.
    """

    inputDataSource: str
    s3: StateMachineInputS3Object
    datasetRevisionId: str
    datasetType: str
    overwriteInputDataset: bool = False


class StateMachineURLPayload(BaseModel):
    """
    Class to hold information about state machine payload data from url.
    """

    inputDataSource: str
    url: str
    datasetRevisionId: str
    datasetType: str
    publishDatasetRevision: bool = False
    overwriteInputDataset: bool = False
