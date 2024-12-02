"""
Setup for Transforming Data
"""

from pytest_factoryboy import register

from tests.timetables_etl.factories.database.organisation import (
    OrganisationDatasetRevisionFactory,
    OrganisationTXCFileAttributesFactory,
)
from tests.timetables_etl.factories.database.transmodel import (
    TransmodelVehicleJourneyFactory,
)

register(OrganisationDatasetRevisionFactory)
register(OrganisationTXCFileAttributesFactory)
register(TransmodelVehicleJourneyFactory)
