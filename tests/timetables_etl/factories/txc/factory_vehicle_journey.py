"""
VJ Factory
"""

import factory
from common_layer.xml.txc.models.txc_operating_profile import (
    TXCDaysOfWeek,
    TXCOperatingProfile,
)
from common_layer.xml.txc.models.txc_vehicle_journey import TXCVehicleJourney


class TXCDaysOfWeekFactory(factory.DictFactory):
    """Factory for TXCDaysOfWeek"""

    class Meta:  # type: ignore[misc]
        model = TXCDaysOfWeek

    Monday = True
    Tuesday = True
    Wednesday = True
    Thursday = True
    Friday = True
    Saturday = False
    Sunday = False
    HolidaysOnly = False


class TXCOperatingProfileFactory(factory.DictFactory):
    """Factory for TXCOperatingProfile"""

    class Meta:  # type: ignore[misc]
        model = TXCOperatingProfile

    RegularDayType = factory.SubFactory(TXCDaysOfWeekFactory)


class TXCVehicleJourneyFactory(factory.DictFactory):
    """Factory for TXCVehicleJourney"""

    class Meta:  # type: ignore[misc]
        model = TXCVehicleJourney

    VehicleJourneyCode = factory.Sequence(lambda n: f"VJ{n}")
    DepartureTime = "09:00"
    JourneyPatternRef = "JP1"
    OperatingProfile = None
