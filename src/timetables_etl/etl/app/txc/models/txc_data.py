"""
TXC Model
"""

from pydantic import BaseModel, Field

from .txc_journey_pattern import TXCJourneyPatternSection
from .txc_metadata import TXCMetadata
from .txc_operator import TXCOperator
from .txc_route import TXCRoute, TXCRouteSection
from .txc_service import TXCService
from .txc_serviced_organisation import TXCServicedOrganisation
from .txc_stoppoint import AnnotatedStopPointRef, TXCStopPoint
from .txc_vehicle_journey import TXCVehicleJourney
from .txc_vehicle_journey_flexible import TXCFlexibleVehicleJourney


class TXCData(BaseModel):
    """
    Top Level Model for TransXChange Data
    """

    Metadata: TXCMetadata | None = Field(default=None, description="File Metadata")
    ServicedOrganisations: list[TXCServicedOrganisation] = Field(default=[])
    StopPoints: list[AnnotatedStopPointRef | TXCStopPoint] = Field(
        default=[], description=""
    )
    RouteSections: list[TXCRouteSection] = Field(default=[], description="")
    Routes: list[TXCRoute] = Field(default=[], description="")
    JourneyPatternSections: list[TXCJourneyPatternSection] = Field(
        default=[], description=""
    )
    Operators: list[TXCOperator] = Field(default=[], description="")
    Services: list[TXCService] = Field(default=[], description="")
    VehicleJourneys: list[TXCVehicleJourney | TXCFlexibleVehicleJourney] = Field(
        default=[], description=""
    )
