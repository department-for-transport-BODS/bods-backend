"""
Pydantic Models / Dataclasses for ClamAV Scanner Lambda
"""

from dataclasses import dataclass
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ClamAVScannerInputData(BaseModel):
    """
    Lambda Input Data
    """

    model_config = ConfigDict(populate_by_name=True)

    s3_bucket_name: Annotated[str, Field(alias="Bucket")]
    s3_file_key: Annotated[str, Field(alias="ObjectKey")]
    revision_id: Annotated[int, Field(alias="DatasetRevisionId")]
    dataset_etl_task_result_id: Annotated[int, Field(alias="DatasetEtlTaskResultId")]
    skip_virus_scan: Annotated[bool, Field(alias="SkipVirusScan", default=False)]


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
