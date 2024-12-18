"""
Flexible Service Factories
"""

import factory
from common_layer.txc.models import (
    TXCBookingArrangements,
    TXCFixedStopUsage,
    TXCFlexibleJourneyPattern,
    TXCFlexibleService,
    TXCFlexibleStopUsage,
    TXCPhone,
)


class TXCPhoneFactory(factory.DictFactory):
    """Factory for TXCPhone"""

    class Meta:  # type: ignore[misc]
        model = TXCPhone

    TelNationalNumber = "0000 000 0000"


class TXCBookingArrangementsFactory(factory.DictFactory):
    """Factory for TXCBookingArrangements"""

    class Meta:  # type: ignore[misc]
        model = TXCBookingArrangements

    Description = "The booking office is open Monday to Friday 8:30am - 6:30pm"
    Phone = factory.SubFactory(TXCPhoneFactory)
    Email = "example@example.com"
    WebAddress = "https://example.com/"
    AllBookingsTaken = True


class TXCFixedStopUsageFactory(factory.DictFactory):
    """Factory for TXCFixedStopUsage"""

    class Meta:  # type: ignore[misc]
        model = TXCFixedStopUsage

    StopPointRef = factory.Sequence(lambda n: f"Stop{n}")
    TimingStatus = "principalTimingPoint"


class TXCFlexibleStopUsageFactory(factory.DictFactory):
    """Factory for TXCFlexibleStopUsage"""

    class Meta:  # type: ignore[misc]
        model = TXCFlexibleStopUsage

    StopPointRef = factory.Sequence(lambda n: f"Stop{n}")


class TXCFlexibleJourneyPatternFactory(factory.DictFactory):
    """Factory for TXCFlexibleJourneyPattern"""

    class Meta:  # type: ignore[misc]
        model = TXCFlexibleJourneyPattern

    id = factory.Sequence(lambda n: f"jp_{n}")
    Direction = "outbound"
    StopPointsInSequence = factory.List(
        [
            factory.SubFactory(
                TXCFixedStopUsageFactory,
                StopPointRef="02903501",
                TimingStatus="otherPoint",
            ),
            factory.SubFactory(TXCFlexibleStopUsageFactory, StopPointRef="02901353"),
        ]
    )
    BookingArrangements = factory.SubFactory(TXCBookingArrangementsFactory)


class TXCFlexibleServiceFactory(factory.DictFactory):
    """Factory for TXCFlexibleService"""

    class Meta:  # type: ignore[misc]
        model = TXCFlexibleService

    Origin = "Market Rasen"
    Destination = "Market Rasen"
    UseAllStopPoints = False
    FlexibleJourneyPattern = factory.List(
        [factory.SubFactory(TXCFlexibleJourneyPatternFactory)]
    )
