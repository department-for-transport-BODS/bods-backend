"""
Type Alises etc
"""

from typing import TypeAlias

from common_layer.database.models import (
    NaptanStopPoint,
    TransmodelServicedOrganisations,
    TransmodelTracks,
)
from common_layer.txc.models.txc_stoppoint import TXCStopPoint

TrackLookup: TypeAlias = dict[tuple[str, str], TransmodelTracks]
ServicedOrgLookup: TypeAlias = dict[str, TransmodelServicedOrganisations]
StopsLookup: TypeAlias = dict[str, NaptanStopPoint]
