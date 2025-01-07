"""
SQL Alchemy Repos for Tables prefixed with data_quality_
"""

from common_layer.pti.models import Violation
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
    def __init__(self, db: SqlDB):
        super().__init__(db, DataQualityPTIObservation)

    def _get_observation_from_violation(
        self, revision_id: int, violation: Violation
    ) -> DataQualityPTIObservation:
        return DataQualityPTIObservation(
            revision_id=revision_id,
            line=violation.line,
            filename=violation.filename,
            element=violation.name,
            details=violation.observation.details,
            category=violation.observation.category,
            reference=violation.observation.reference,
        )

    def create_from_violations(
        self, revision_id: int, violations: list[Violation]
    ) -> bool:
        """
        Creates PTIObservations for the given revision id and list of violations
        """
        try:
            db_objects = [
                self._get_observation_from_violation(revision_id, violation)
                for violation in violations
            ]
            self.bulk_insert(db_objects)
        except Exception as e:
            logger.info(str(e))
            raise

        return True
