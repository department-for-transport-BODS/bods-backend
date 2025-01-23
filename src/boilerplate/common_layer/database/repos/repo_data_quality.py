"""
SQL Alchemy Repos for Tables prefixed with data_quality_
"""

from structlog.stdlib import get_logger

from ..client import SqlDB
from ..models.model_data_quality import (
    DataQualityPostSchemaViolation,
    DataQualityPTIObservation,
    DataQualitySchemaViolation,
)
from .repo_common import BaseRepositoryWithId

logger = get_logger()


class DataQualitySchemaViolationRepo(BaseRepositoryWithId[DataQualitySchemaViolation]):
    """Repository for managing Data Quality Schema Violation entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, DataQualitySchemaViolation)


class DataQualityPostSchemaViolationRepo(
    BaseRepositoryWithId[DataQualityPostSchemaViolation]
):
    """Repository for managing Data Quality Post Schema Violation entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, DataQualityPostSchemaViolation)


class DataQualityPTIObservationRepo(BaseRepositoryWithId[DataQualityPTIObservation]):
    """
    DataQuality PTI Observation
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, DataQualityPTIObservation)
