"""
Dataclasses to group data being passed in the ETL process
"""

from dataclasses import dataclass

from .types import ServicedOrgLookup, StopsLookup, TrackLookup


@dataclass
class ReferenceDataLookups:
    """Collection of lookup dictionaries for TransXChange processing"""

    stops: StopsLookup
    serviced_orgs: ServicedOrgLookup
    tracks: TrackLookup
