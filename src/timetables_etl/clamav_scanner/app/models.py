"""
Pydantic Models / Dataclasses for ClamAV Scanner Lambda
"""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field


class ClamAVScannerInputData(BaseModel):
    """
    Lambda Input Data
    """

    model_config = ConfigDict(populate_by_name=True)

    s3_bucket_name: str = Field(alias="Bucket")
    s3_file_key: str = Field(alias="ObjectKey")
    revision_id: int = Field(alias="DatasetRevisionId")
    dataset_etl_task_result_id: int = Field(alias="DatasetEtlTaskResultId")


class ClamAVConfig(BaseModel):
    """
    Config Vars for ClamAV
    """

    host: str
    port: int


@dataclass
class ScanResult:
    """
    Virus Scan Result with Optional Reason
    """

    status: str
    reason: str | None = None
