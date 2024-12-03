"""
Flexible Journey TM Repos
"""

from timetables_etl.etl.app.database.client import BodsDB
from timetables_etl.etl.app.database.models.model_transmodel_flexible import (
    TransmodelBookingArrangements,
    TransmodelFlexibleServiceOperationPeriod,
)
from timetables_etl.etl.app.database.repos.repo_common import BaseRepositoryWithId


class TransmodelBookingArrangementsRepo(
    BaseRepositoryWithId[TransmodelBookingArrangements]
):
    """Repository for managing Booking Arrangements entities"""

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelBookingArrangements)


class TransmodelFlexibleServiceOperationPeriodRepo(
    BaseRepositoryWithId[TransmodelFlexibleServiceOperationPeriod]
):
    """Repository for managing Flexible Service Operation Period entities"""

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelFlexibleServiceOperationPeriod)
