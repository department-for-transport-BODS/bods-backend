"""
Dataclasses to group data being passed in the ETL process
"""

from dataclasses import dataclass

from ..types import FlexibleZoneLookup, ServicedOrgLookup, StopsLookup, TrackLookup


@dataclass
class ReferenceDataLookups:
    """Collection of lookup dictionaries for TransXChange processing"""

    stops: StopsLookup
    flexible_zone_locations: FlexibleZoneLookup
    serviced_orgs: ServicedOrgLookup
    tracks: TrackLookup
