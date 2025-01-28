"""
Type Alises etc
"""

from typing import TypeAlias

from common_layer.database.models import (
    NaptanStopPoint,
    TransmodelServicedOrganisations,
    TransmodelTracks,
)

TrackLookup: TypeAlias = dict[tuple[str, str], TransmodelTracks]
ServicedOrgLookup: TypeAlias = dict[str, TransmodelServicedOrganisations]
StopsLookup: TypeAlias = dict[str, NaptanStopPoint]
