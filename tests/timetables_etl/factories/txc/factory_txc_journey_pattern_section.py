"""
Journey Pattern Section Factories
"""

import factory
from common_layer.txc.models import (
    TXCJourneyPatternSection,
    TXCJourneyPatternStopUsage,
    TXCJourneyPatternTimingLink,
)


class TXCJourneyPatternStopUsageFactory(factory.DictFactory):
    """Factory for TXCJourneyPatternStopUsage"""

    class Meta:  # type: ignore[misc]
        model = TXCJourneyPatternStopUsage

    id = factory.Sequence(lambda n: f"JPSU{n}")
    Activity = "pickUpAndSetDown"
    StopPointRef = factory.Sequence(lambda n: f"490{n:06d}")
    TimingStatus = "principalTimingPoint"


class TXCJourneyPatternTimingLinkFactory(factory.DictFactory):
    """Factory for TXCJourneyPatternTimingLink"""

    class Meta:  # type: ignore[misc]
        model = TXCJourneyPatternTimingLink

    id = factory.Sequence(lambda n: f"JPTL{n}")
    From = factory.SubFactory(TXCJourneyPatternStopUsageFactory)
    To = factory.SubFactory(TXCJourneyPatternStopUsageFactory)
    RouteLinkRef = factory.LazyAttribute(lambda o: f"RL_{o.id}")
    RunTime = "PT0H0M0S"


class TXCJourneyPatternSectionFactory(factory.DictFactory):
    """Factory for TXCJourneyPatternSection"""

    class Meta:  # type: ignore[misc]
        model = TXCJourneyPatternSection

    id = factory.Sequence(lambda n: f"JPS{n}")
    JourneyPatternTimingLink = factory.List(
        [factory.SubFactory(TXCJourneyPatternTimingLinkFactory)]
    )
