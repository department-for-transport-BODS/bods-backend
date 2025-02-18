"""
Shared Types / Enums / Literals for Netex
"""

from typing import Literal

LineTypeT = Literal[
    "local",
    "urban",
    "longDistance",
    "express",
    "seasonal",
    "replacement",
    "flexible",
    "other",
]

ProofOfIdentityT = Literal[
    "noneRequired",
    "creditCard",
    "passport",
    "drivingLicence",
    "birthCertificate",
    "membershipCard",
    "identityDocument",
    "medicalDocument",
    "studentCard",
    "letterWIthAddress",
    "mobileDevice",
    "emailAccount",
    "measurement",
    "other",
]

DiscountBasisT = Literal["none", "free", "discount"]

UsageTriggerT = Literal[
    "enrolment",
    "reservation",
    "purchase",
    "fulfilment",
    "activation",
    "specifiedStartDate",
    "startOutboundRide",
    "endOutboundRide",
    "startReturnRide",
    "startOfPeriod",
    "dayOffsetBeforeCalendarPeriod",
]
ActivationMeansT = Literal[
    "noneRequired",
    "checkIn",
    "useOfValidator",
    "useOfMobileDevice",
    "automaticByTime",
    "automaticByProximity",
    "other",
]

UsageEndT = Literal[
    "standardDuration",
    "endOfCalendarPeriod",
    "endOfRide",
    "endOfTrip",
    "endOfFareDay",
    "endOfFarePeriod",
    "productExpiry",
    "profileExpiry",
    "deregistration",
    "other",
]


TariffBasisT = Literal[
    "flat",
    "distance",
    "unitSection",
    "zone",
    "zoneToZone",
    "pointToPoint",
    "route",
    "tour",
    "group",
    "discount",
    "period",
    "free",
    "other",
]

PreassignedFareProductTypeT = Literal[
    "singleTrip",
    "shortTrip",
    "timeLimitedSingleTrip",
    "dayReturnTrip",
    "periodReturnTrip",
    "multistepTrip",
    "dayPass",
    "periodPass",
    "supplement",
    "other",
]

ChargingMomentTypeT = Literal[
    "beforeTravel",
    "onStartOfTravel",
    "beforeEndOfTravel",
    "onStartThenAdjustAtEndOfTravel",
    # Note: there's a typo in the XSD ("onStarThen" vs "onStartThen")
    "onStarThenAdjustAtEndOfFareDay",
    "onStartThenAdjustAtEndOfChargePeriod",
    "atEndOfTravel",
    "atEndOfFareDay",
    "atEndOfChargePeriod",
    "free",
    "anyTime",
    "other",
]

UserTypeT = Literal[
    "adult",
    "child",
    "infant",
    "senior",
    "student",
    "youngPerson",
    "schoolPupil",
    "military",
    "disabled",
    "disabledCompanion",
    "jobSeeker",
    "employee",
    "animal",
    "anyone",
]
