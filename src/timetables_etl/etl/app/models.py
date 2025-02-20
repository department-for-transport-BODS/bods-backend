"""
Pydantic Models 
"""

from typing import Self

from common_layer.database.models import (
    DatasetETLTaskResult,
    OrganisationDatasetRevision,
    OrganisationTXCFileAttributes,
)
from pydantic import BaseModel, ConfigDict, Field


class ETLInputData(BaseModel):
    """
    Input data for the ETL Function
    """

    model_config = ConfigDict(populate_by_name=True)

    task_id: int = Field(alias="DatasetEtlTaskResultId")
    file_attributes_id: int = Field(alias="fileAttributesId")
    s3_bucket_name: str = Field(alias="Bucket")
    s3_file_key: str = Field(alias="ObjectKey")


class TaskData(BaseModel):
    """
    Task information to be passed around
    """

    model_config = ConfigDict(frozen=True)

    etl_task: DatasetETLTaskResult
    revision: OrganisationDatasetRevision
    file_attributes: OrganisationTXCFileAttributes
    input_data: ETLInputData


class PatternCommonStats(BaseModel):
    """
    Service Pattern Common Stats
    """

    localities: int = 0
    admin_areas: int = 0
    vehicle_journeys: int = 0
    pattern_stops: int = 0
    tracks: int = 0

    def __iadd__(self, other: Self) -> Self:
        """
        Add another PatternCommonStats instance to this one in-place.

        """
        if not isinstance(other, PatternCommonStats):
            raise TypeError(
                f"unsupported for +=: '{type(self).__name__}' and '{type(other).__name__}'"
            )

        self.localities += other.localities
        self.admin_areas += other.admin_areas
        self.vehicle_journeys += other.vehicle_journeys
        self.pattern_stops += other.pattern_stops
        self.tracks += other.tracks

        return self


class ETLProcessStats(BaseModel):
    """
    Stats for what was processed by the ETL Process overall
    """

    services: int = 0
    booking_arrangements: int = 0
    service_patterns: int = 0
    pattern_stats: PatternCommonStats = PatternCommonStats()
