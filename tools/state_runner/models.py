"""
Model definition for state runner
"""

from pydantic import BaseModel


class StateMachineInputS3Bucket(BaseModel):
    """
    Class to hold information about S3 bucket.
    """

    name: str


class StateMachineInputS3ObjectKey(BaseModel):
    """
    Class to hold information about S3 object key.
    """

    key: str


class StateMachineInputS3Details(BaseModel):
    """
    Class to hold information about state machine payload details.
    """

    bucket: StateMachineInputS3Bucket
    object: StateMachineInputS3ObjectKey
    datasetRevisionId: str
    datasetType: str


class StateMachineInputPayload(BaseModel):
    """
    Class to hold information about state machine payload events.
    """

    detail: StateMachineInputS3Details
