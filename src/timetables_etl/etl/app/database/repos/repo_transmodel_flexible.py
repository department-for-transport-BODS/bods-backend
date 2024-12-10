"""
Flexible Journey TM Repos
"""

from ..client import BodsDB
from ..models import (
    TransmodelBookingArrangements,
    TransmodelFlexibleServiceOperationPeriod,
)
from ..repos.repo_common import BaseRepositoryWithId


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
