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
TransportModeT = Literal[
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
    "busCoachStationAccessArea",
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

JourneyPatternVehicleDirectionT = Literal[
    "inbound",
    "outbound",
    "inboundAndOutbound",
    "circular",
    "clockwise",
    "antiClockwise",
    # Inherit is default specified in TXC XSD
    "inherit",
]
DirectionT = Literal["inbound", "outbound", "clockwise", "anticlockwise"]

# Mappings

# Use TXC Recommended values instead of codes
STOP_CLASSIFICATION_STOP_TYPE_MAPPING: dict[str, str] = {
    # Bus/Coach stops
    "BCT": "busCoachTrolleyOnStreetPoint",
    "BCS": "busCoachTrolleyStationBay",
    "BCQ": "busCoachTrolleyStationVariableBay",
    "BST": "busCoachStationAccessArea",
    "BCE": "busCoachTrolleyStationEntrance",
    # Rail stops
    "RPL": "railPlatform",
    "RLY": "railAccessArea",
    "RSE": "railStationEntrance",
    # Tram/Metro/Underground stops
    "PLT": "tramMetroUndergroundPlatform",
    "MET": "tramMetroUndergroundAccessArea",
    "TMU": "tramMetroUndergroundStationEntrance",
    # Ferry stops
    "FBT": "ferryBerth",
    "FER": "ferryDockAccessArea",
    "FTD": "ferryTerminalDockEntrance",
    # Taxi ranks
    "TXR": "taxiRank",
    "STR": "sharedTaxiRank",
    # Airport
    "AIR": "airportEntrance",
    "GAT": "airAccessArea",
    # Other transport modes
    "SDA": "carSetDownPickUpArea",
    "LSE": "liftOrCableCarStationEntrance",
    "LCB": "liftOrCableCarAccessArea",
    "LPL": "liftOrCableCarPlatform",
    # Deprecated mappings
    "busCoachTramStationEntrance": "busCoachTrolleyStationEntrance",
    "busCoachTramStationBay": "busCoachTrolleyStationBay",
    "busCoachTramStationVariableBay": "busCoachTrolleyStationBay",
    "busCoachTramOnStreetPoint": "busCoachTrolleyOnStreetPoint",
    "FerryBerth": "ferryBerth",
}


# Correct Spelling Mistakes in Timing Status from older TXC Standards
# Also conver to full names
TIMING_STATUS_MAPPING: dict[str, TimingStatusT] = {
    # Map 3 letters to the new full names
    # TXC has had versions with spelling mistakes that map onto new names
    "PPT": "principalPoint",
    "principalPoint": "principalPoint",
    "principlePoint": "principalPoint",  # Deprecated spelling mistake
    "TIP": "timeInfoPoint",
    "timeInfoPoint": "timeInfoPoint",
    "PTP": "principalTimingPoint",
    "principalTimingPoint": "principalTimingPoint",
    "principleTimingPoint": "principalTimingPoint",  # Deprecated spelling mistake
    "OTH": "otherPoint",
    "otherPoint": "otherPoint",
}
