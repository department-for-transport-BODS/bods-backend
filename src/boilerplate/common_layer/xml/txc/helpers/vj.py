"""
Vehicle Journey Helpers
"""

from ..models import TXCFlexibleVehicleJourney, TXCVehicleJourney


def map_vehicle_journeys_to_lines(
    vjs: (
        list[TXCVehicleJourney | TXCFlexibleVehicleJourney]
        | list[TXCVehicleJourney]
        | list[TXCFlexibleVehicleJourney]
    ),
) -> dict[str, list[str]]:
    """
    Create a mapping between line IDs and vehicle journey codes
    """
    line_to_vehicle_journeys: dict[str, list[str]] = {}

    for vj in vjs:
        if vj.LineRef and vj.VehicleJourneyCode:
            if vj.LineRef not in line_to_vehicle_journeys:
                line_to_vehicle_journeys[vj.LineRef] = []

            line_to_vehicle_journeys[vj.LineRef].append(vj.VehicleJourneyCode)

    return line_to_vehicle_journeys
