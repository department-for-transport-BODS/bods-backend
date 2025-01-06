"""
SQL Alchemy Repos for Tables prefixed with data_quality_
"""

from ..client import SqlDB
from ..models.model_data_quality import DataQualitySchemaViolation
from .repo_common import BaseRepositoryWithId


class DataQualitySchemaViolationRepo(BaseRepositoryWithId[DataQualitySchemaViolation]):
    """Repository for managing Data Quality Schema Violation entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, DataQualitySchemaViolation)
