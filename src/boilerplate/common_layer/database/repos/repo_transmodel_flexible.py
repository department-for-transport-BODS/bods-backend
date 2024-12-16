"""
Flexible Journey TM Repos
"""

from ..client import SqlDB
from ..models import (
    TransmodelBookingArrangements,
    TransmodelFlexibleServiceOperationPeriod,
)
from ..repos.repo_common import BaseRepositoryWithId


class TransmodelBookingArrangementsRepo(
    BaseRepositoryWithId[TransmodelBookingArrangements]
):
    """Repository for managing Booking Arrangements entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, TransmodelBookingArrangements)

    def get_by_service_ids(
        self, service_ids: list[int]
    ) -> list[TransmodelBookingArrangements]:
        """
        Get booking arrangements by service ids
        """
        if not service_ids:
            return []
        statement = self._build_query().where(self._model.service_id.in_(service_ids))
        return self._fetch_all(statement)


class TransmodelFlexibleServiceOperationPeriodRepo(
    BaseRepositoryWithId[TransmodelFlexibleServiceOperationPeriod]
):
    """Repository for managing Flexible Service Operation Period entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, TransmodelFlexibleServiceOperationPeriod)

    def get_by_vehicle_journey_ids(
        self, vehicle_journey_ids: list[int]
    ) -> list[TransmodelFlexibleServiceOperationPeriod]:
        """
        Get flexible service operation period by journey ids.
        """
        if not vehicle_journey_ids:
            return []
        statement = self._build_query().where(
            self._model.vehicle_journey_id.in_(vehicle_journey_ids)
        )
        return self._fetch_all(statement)
