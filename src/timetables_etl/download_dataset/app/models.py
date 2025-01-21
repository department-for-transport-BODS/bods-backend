"""
DownloadData Pydantic Models and Dataclasses
"""

from dataclasses import dataclass

from pydantic import AnyUrl, BaseModel, ConfigDict, Field


class DownloadDatasetInputData(BaseModel):
    """
    Input data for the download dataset function
    """

    model_config = ConfigDict(populate_by_name=True)

    task_id: int = Field(alias="DatasetEtlTaskResultId")
    s3_bucket_name: str = Field(alias="Bucket")
    s3_file_key: str = Field(alias="ObjectKey")
    remote_dataset_url_link: AnyUrl = Field(alias="URLLink")
    revision_id: int = Field(alias="DatasetRevisionId")


@dataclass
class DownloaderResponse:
    """
    Pydantic model that represents the response from a file download operation.

    This model is used to capture the file type (e.g., MIME type or file extension)
    and the binary content of the downloaded file.
    """

    filetype: str
    content: bytes
