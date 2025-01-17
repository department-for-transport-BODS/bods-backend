"""
Model definition for state runner
"""

from pydantic import BaseModel


class Bucket(BaseModel):
    """
    Class to hold information about S3 bucket.
    """

    name: str


class Object(BaseModel):
    """
    Class to hold information about S3 object key.
    """

    key: str


class Detail(BaseModel):
    """
    Class to hold information about state machine payload details.
    """

    bucket: Bucket
    object: Object
    datasetRevisionId: str
    datasetType: str


class Event(BaseModel):
    """
    Class to hold information about state machine payload events.
    """

    detail: Detail
