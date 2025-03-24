from common_layer.xml.txc.models import (
    TXCData,
    TXCFlexibleJourneyPattern,
    TXCFlexibleService,
    TXCJourneyPattern,
    TXCService,
    TXCStandardService,
)

from tests.timetables_etl.factories.txc.factory_txc_data import (
    TXCDataFactory,
    TXCServiceFactory,
    TXCStandardServiceFactory,
)
from timetables_etl.etl.app.load.vehicle_journey.vehicle_journey import (
    get_journey_pattern_lookup,
)


def test_get_journey_pattern_lookup():
    """
    Test that JPs from both standard and flexible services are included in lookup
    """

    journey_pattern_1 = TXCJourneyPattern.model_construct(id="jp_1")
    journey_pattern_2 = TXCJourneyPattern.model_construct(id="jp_2")

    flexible_jp_1 = TXCFlexibleJourneyPattern.model_construct(id="jp_3")
    flexible_jp_2 = TXCFlexibleJourneyPattern.model_construct(id="jp_4")

    expected_result = {
        "jp_1": journey_pattern_1,
        "jp_2": journey_pattern_2,
        "jp_3": flexible_jp_1,
        "jp_4": flexible_jp_2,
    }

    standard_service = TXCStandardServiceFactory.create(
        JourneyPattern=[journey_pattern_1, journey_pattern_2],
    )
    flexible_service = TXCFlexibleService.model_construct(
        FlexibleJourneyPattern=[flexible_jp_1, flexible_jp_2],
    )

    txc_data = TXCDataFactory.create(
        Services=[
            TXCServiceFactory.create(StandardService=standard_service),
            TXCServiceFactory.create(FlexibleService=flexible_service),
        ]
    )

    lookup = get_journey_pattern_lookup(txc_data)

    assert lookup == expected_result
