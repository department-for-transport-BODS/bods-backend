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
