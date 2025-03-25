"""
Type Alises etc
"""

from typing import TypeAlias

from common_layer.database.models import (
    NaptanStopPoint,
    TransmodelServicedOrganisations,
    TransmodelTracks,
)
from common_layer.xml.txc.models import LocationStructure

from .dataclasses.stop_points import NonExistentNaptanStop

TrackLookup: TypeAlias = dict[tuple[str, str], TransmodelTracks]
ServicedOrgLookup: TypeAlias = dict[str, TransmodelServicedOrganisations]

LookupStopPoint: TypeAlias = NaptanStopPoint | NonExistentNaptanStop
StopsLookup: TypeAlias = dict[str, LookupStopPoint]
FlexibleZoneLookup: TypeAlias = dict[str, list[LocationStructure]]
