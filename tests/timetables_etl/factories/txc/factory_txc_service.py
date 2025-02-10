"""
Factories for a TXC Service
"""

from datetime import date

import factory
from common_layer.xml.txc.models import (
    TXCJourneyPattern,
    TXCLine,
    TXCLineDescription,
    TXCService,
    TXCStandardService,
)

from .factory_txc_service_flexible import TXCFlexibleServiceFactory


class TXCLineDescriptionFactory(factory.DictFactory):
    """Factory for TXCLineDescription"""

    class Meta:  # type: ignore[misc]
        model = TXCLineDescription

    Origin = factory.Sequence(lambda n: f"Origin{n}")
    Destination = factory.Sequence(lambda n: f"Destination{n}")
    Description = factory.LazyAttribute(lambda o: f"{o.Origin} - {o.Destination}")
    Vias = []

    class Params:
        """Factory parameters for different description scenarios"""

        inbound = factory.Trait(
            Origin="Plymouth",
            Destination="London",
            Description="Plymouth - London",
        )
        outbound = factory.Trait(
            Origin="London",
            Destination="Plymouth",
            Description="London - Plymouth",
        )


class TXCLineFactory(factory.DictFactory):
    """Factory for TXCLine"""

    class Meta:  # type: ignore[misc]
        model = TXCLine

    id = factory.Sequence(lambda n: f"LINE:{n}")
    LineName = factory.Sequence(lambda n: f"Line{n}")
    MarketingName = None
    OutboundDescription = None
    InboundDescription = None

    class Params:
        """Factory parameters for different line scenarios"""

        standard = factory.Trait(
            id="FLIX:UZ000FLIX:UK045:UK045",
            LineName="UK045",
            OutboundDescription=factory.SubFactory(
                TXCLineDescriptionFactory, outbound=True
            ),
            InboundDescription=factory.SubFactory(
                TXCLineDescriptionFactory, inbound=True
            ),
        )
        with_descriptions = factory.Trait(
            OutboundDescription=factory.SubFactory(
                TXCLineDescriptionFactory, outbound=True
            ),
            InboundDescription=factory.SubFactory(
                TXCLineDescriptionFactory, inbound=True
            ),
        )


class TXCJourneyPatternFactory(factory.DictFactory):
    """Factory for TXCJourneyPattern"""

    class Meta:  # type: ignore[misc]
        model = TXCJourneyPattern

    id = factory.Sequence(lambda n: f"JP{n}")
    DestinationDisplay = "Victoria - Plymouth"
    Direction = "inbound"
    RouteRef = "R1"
    JourneyPatternSectionRefs = ["JPS1"]


class TXCStandardServiceFactory(factory.DictFactory):
    """Factory for TXCStandardService"""

    class Meta:  # type: ignore[misc]
        model = TXCStandardService

    Origin = "London"
    Destination = "Plymouth"
    JourneyPattern = []


class TXCServiceFactory(factory.DictFactory):
    """Factory for TXCService"""

    class Meta:  # type: ignore[misc]
        model = TXCService

    RevisionNumber = 1
    ServiceCode = "UZ000FLIX:UK045"
    PrivateCode = "UK045"
    RegisteredOperatorRef = "FLIX"
    PublicUse = True
    StartDate = date(2024, 11, 11)
    EndDate = date(2025, 1, 5)
    StandardService = factory.SubFactory(TXCStandardServiceFactory)
    FlexibleService = None
    Lines = factory.List([factory.SubFactory(TXCLineFactory)])
    Mode = "coach"

    class Params:
        """Factory parameters"""

        no_lines = factory.Trait(Lines=[])
        simple_line = factory.Trait(
            Lines=factory.List([factory.SubFactory(TXCLineFactory, simple=True)])
        )
        with_standard_line = factory.Trait(
            Lines=factory.List([factory.SubFactory(TXCLineFactory, standard=True)])
        )
        flexible = factory.Trait(
            ServiceCode="PB0002032:467",
            RegisteredOperatorRef="O1",
            StartDate=date(2022, 1, 1),
            EndDate=None,
            StandardService=None,
            FlexibleService=factory.SubFactory(TXCFlexibleServiceFactory),
            Lines=factory.List([factory.SubFactory(TXCLineFactory, LineName="53M")]),
        )

    @classmethod
    def without_end_date(cls, **kwargs) -> TXCService:
        """Creates a service with no end date for testing date handling"""
        return cls.create(EndDate=None, **kwargs)

    @classmethod
    def multiple_lines(cls, line_names: list[str], **kwargs) -> TXCService:
        """Creates a service with multiple line names for testing line name collection"""
        return cls.create(
            Lines=[TXCLineFactory(LineName=name) for name in line_names], **kwargs
        )

    @classmethod
    def with_no_origin_destination(cls, **kwargs) -> TXCService:
        """Creates a service with empty origin/destination for testing fallbacks"""
        return cls.create(
            StandardService=TXCStandardServiceFactory(Origin="", Destination=""),
            **kwargs,
        )

    @classmethod
    def flexible_with_origin_destination(
        cls, origin: str, destination: str, **kwargs
    ) -> TXCService:
        """Creates a flexible service with specific origin/destination"""
        return cls.create(
            StandardService=None,
            FlexibleService=TXCFlexibleServiceFactory(
                Origin=origin, Destination=destination
            ),
            **kwargs,
        )

    @classmethod
    def non_public_use(cls, **kwargs) -> TXCService:
        """Creates a non-public service for testing public_use field"""
        return cls.create(PublicUse=False, **kwargs)
