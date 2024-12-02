"""
Types for TXC
"""

from typing import Literal

ServiceOrganisationClassificationT = Literal[
    "school",
    "office",
    "retailSite",
    "touristAttraction",
    "market",
    "factory",
    "college",
    "military",
    "sportsFacility",
    "eventVenue",
    "other",
]

ModificationType = Literal["new", "delete", "revise", "delta"]
StatusT = Literal["active", "inactive", "pending"]
TransportModeType = Literal[
    "air",
    "bus",
    "coach",
    "ferry",
    "metro",
    "rail",
    "tram",
    "trolleyBus",
    "underground",
]
CompassPointT = Literal["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
BusStopTypeT = Literal[
    "MKD", "marked", "HAR", "hailAndRide", "CUS", "custom", "FLX", "flexible"
]
TimingStatusT = Literal[
    "principalTimingPoint", "timeInfoPoint", "otherPoint", "principalPoint"
]
TXCStopTypeT = Literal[
    "airAccessArea",
    "airportEntrance",
    "busCoachTrolleyOnStreetPoint",
    "busCoachTrolleyStationBay",
    "busCoachTrolleyStationEntrance",
    "busCoachTrolleyStationVariableBay",
    "carSetDownPickUpArea",
    "ferryBerth",
    "ferryDockAccessArea",
    "ferryTerminalDockEntrance",
    "liftOrCableCarAccessArea",
    "liftOrCableCarPlatform",
    "liftOrCableCarStationEntrance",
    "railAccessArea",
    "railPlatform",
    "railStationEntrance",
    "sharedTaxiRank",
    "taxiRank",
    "tramMetroUndergroundAccessArea",
    "tramMetroUndergroundPlatform",
    "tramMetroUndergroundStationEntrance",
]
TimeDemandT = Literal[
    "earlyMorning",
    "offPeak",
    "peakMorning",
    "peakAfternoon",
    "evening",
    "lateEvening",
    "saturdayMorning",
    "saturdayDaytime",
    "saturdayEvening",
    "sunday",
    "bankHoliday",
]
CommercialBasisT = Literal["contracted", "notContracted", "partContracted", "unknown"]
ActivityT = Literal["pickUpAndSetDown", "pickUp", "setDown", "pass"]
LicenceClassificationT = Literal[
    "standardNational",
    "standardInternational",
    "restricted",
    "specialRestricted",
    "communityBusPermit",
]

DirectionT = Literal["inbound", "outbound", "clockwise", "anticlockwise"]
