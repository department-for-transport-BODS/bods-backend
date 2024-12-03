import logging
from typing import List

from common import BodsDB
from db.models import DataQualityPtiobservation
from exceptions.pipeline_exceptions import PipelineException
from pti_common.models import Violation
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class PTIObservationRepository:
    def __init__(self, db):
        self._db: BodsDB = db

    def _get_observation_from_violation(self, revision_id: int, violation: Violation) -> DataQualityPtiobservation:
        return self._db.classes.data_quality_ptiobservation(
            revision_id=revision_id,
            line=violation.line,
            filename=violation.filename,
            element=violation.name,
            details=violation.observation.details,
            category=violation.observation.category,
            reference=violation.observation.reference,
        )

    def create(self, revision_id: int, violations: List[Violation]) -> bool:
        """
        Creates PTIObservations for the given revision id and list of violations
        """
        with self._db.session as session:
            db_objects = [self._get_observation_from_violation(revision_id, violation) for violation in violations]
            try:
                # session.query(self._db.classes.data_quality_ptiobservation).filter_by(revision_id=revision_id).delete()
                # TODO: Any need to batch writes here?
                session.add_all(db_objects)
                session.commit()
            except SQLAlchemyError as exc:
                session.rollback()
                message = f"Failed to add re-create PTIObservations for revision {revision_id}"
                logger.error(message, exc_info=True)
                raise PipelineException(message) from exc
        return True
