"""
Module for functions related to revision stats
"""

from common_layer.database import SqlDB
from common_layer.database.dataclasses import RevisionStats
from common_layer.database.repos import (
    OrganisationTXCFileAttributesRepo,
    TransmodelServiceRepo,
)


def build_revision_stats(revision_id: int, db: SqlDB) -> RevisionStats:
    """
    Derive revision stats from related TXC file attributes and services.

    Returns creation/modification datetimes and service date ranges for the given revision.
    """
    file_attributes_repo = OrganisationTXCFileAttributesRepo(db)
    service_repo = TransmodelServiceRepo(db)

    txc_file_stats = file_attributes_repo.get_file_datetime_stats_by_revision_id(
        revision_id
    )
    service_stats = service_repo.get_service_stats_by_revision_id(revision_id)

    return RevisionStats(
        publisher_creation_datetime=txc_file_stats.first_creation_datetime,
        publisher_modification_datetime=txc_file_stats.last_modification_datetime,
        first_expiring_service=service_stats.first_expiring_service,
        last_expiring_service=service_stats.last_expiring_service,
        first_service_start=service_stats.first_service_start,
    )
