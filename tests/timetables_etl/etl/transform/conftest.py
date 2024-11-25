"""
Setup for Transforming Data
"""

from pytest_factoryboy import register

from tests.timetables_etl.factories.database.organisation import (
    OrganisationDatasetRevisionFactory,
    OrganisationTXCFileAttributesFactory,
)

register(OrganisationDatasetRevisionFactory)
register(OrganisationTXCFileAttributesFactory)
