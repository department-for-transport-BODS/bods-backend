"""
Vehicle Journey Repos
"""

from ..client import SqlDB
from ..models import (
    TransmodelNonOperatingDatesExceptions,
    TransmodelOperatingDatesExceptions,
    TransmodelOperatingProfile,
    TransmodelVehicleJourney,
)
from ..repos.repo_common import BaseRepositoryWithId


class TransmodelVehicleJourneyRepo(BaseRepositoryWithId[TransmodelVehicleJourney]):
    """
    Repository for managing Transmodel Vehicle Journey entities
    Table: transmodel_vehiclejourney
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, TransmodelVehicleJourney)


class TransmodelOperatingProfileRepo(BaseRepositoryWithId[TransmodelOperatingProfile]):
    """Repository for managing Operating Profile entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, TransmodelOperatingProfile)


class TransmodelOperatingDatesExceptionsRepo(
    BaseRepositoryWithId[TransmodelOperatingDatesExceptions]
):
    """Repository for managing Operating Dates Exceptions entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, TransmodelOperatingDatesExceptions)


class TransmodelNonOperatingDatesExceptionsRepo(
    BaseRepositoryWithId[TransmodelNonOperatingDatesExceptions]
):
    """Repository for managing Non Operating Dates Exceptions entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, TransmodelNonOperatingDatesExceptions)
