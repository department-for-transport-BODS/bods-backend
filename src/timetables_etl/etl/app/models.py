"""
Pydantic Models
"""

from dataclasses import dataclass
from typing import Annotated, Self

from common_layer.database.client import SqlDB
from common_layer.database.models import (
    DatasetETLTaskResult,
    OrganisationDatasetRevision,
    OrganisationTXCFileAttributes,
)
from common_layer.dynamodb.client.naptan_stop_points import (
    NaptanStopPointDynamoDBClient,
)
from common_layer.dynamodb.data_manager import FileProcessingDataManager
from pydantic import BaseModel, ConfigDict, Field


class ETLInputData(BaseModel):
    """
    Input data for the ETL Function
    """

    model_config = ConfigDict(populate_by_name=True)

    task_id: Annotated[int, Field(alias="DatasetEtlTaskResultId")]
    file_attributes_id: Annotated[int, Field(alias="TxcFileAttributesId")]
    s3_bucket_name: Annotated[str, Field(alias="Bucket")]
    s3_file_key: Annotated[str, Field(alias="ObjectKey")]
    superseded_timetable: Annotated[
        bool, Field(alias="SupersededTimetable", default=False)
    ]
    skip_track_inserts: Annotated[
        bool,
        Field(
            alias="SkipTrackInserts",
            default=False,
            description="Skip the insertion of tracks data (used for reprocessing)",
        ),
    ]


class TaskData(BaseModel):
    """
    Task information to be passed around
    """

    model_config = ConfigDict(frozen=True)

    etl_task: DatasetETLTaskResult
    revision: OrganisationDatasetRevision
    file_attributes: OrganisationTXCFileAttributes
    input_data: ETLInputData


@dataclass
class ETLTaskClients:
    """
    Clients required for ETL task
    """

    db: SqlDB
    stop_point_client: NaptanStopPointDynamoDBClient
    dynamo_data_manager: FileProcessingDataManager


class PatternCommonStats(BaseModel):
    """
    Service Pattern Common Stats
    """

    localities: int = 0
    admin_areas: int = 0
    vehicle_journeys: int = 0
    pattern_stops: int = 0
    tracks: int = 0
    distance: int | None = None

    def __iadd__(self, other: Self) -> Self:
        """
        Add another PatternCommonStats instance to this one in-place.

        """
        # Ignore Type to Prevent other types from being added to it
        if not isinstance(other, PatternCommonStats):  # type: ignore
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
    superseded_timetables: int = 0
    booking_arrangements: int = 0
    service_patterns: int = 0
    pattern_stats: PatternCommonStats = PatternCommonStats()
