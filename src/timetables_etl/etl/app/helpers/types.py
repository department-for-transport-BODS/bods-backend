"""
Type Alises etc
"""

from typing import TypeAlias

from common_layer.database.models import (
    NaptanStopPoint,
    TransmodelServicedOrganisations,
    TransmodelTracks,
)

from .stop_points import NonExistentNaptanStop

TrackLookup: TypeAlias = dict[tuple[str, str], TransmodelTracks]
ServicedOrgLookup: TypeAlias = dict[str, TransmodelServicedOrganisations]

LookupStopPoint: TypeAlias = NaptanStopPoint | NonExistentNaptanStop
StopsLookup: TypeAlias = dict[str, LookupStopPoint]
