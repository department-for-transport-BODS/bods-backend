"""
Test Processing Journey Pattern Sections
"""

from datetime import time

import pytest
from common_layer.database.models.model_transmodel import (
    TransmodelServicePattern,
    TransmodelStopActivity,
)
from common_layer.database.models.model_transmodel_vehicle_journey import (
    TransmodelVehicleJourney,
)
from common_layer.xml.txc.models.txc_journey_pattern import TXCJourneyPatternSection
from common_layer.xml.txc.models.txc_vehicle_journey import (
    TXCVehicleJourney,
    TXCVehicleJourneyStopUsageStructure,
    TXCVehicleJourneyTimingLink,
)
from etl.app.transform.service_pattern_stops import (
    GeneratePatternStopsContext,
    JourneySectionContext,
    SectionProcessingState,
    process_journey_pattern_section,
)

from tests.factories.database.naptan import NaptanStopPointFactory
from tests.timetables_etl.factories.txc.factory_txc_journey_pattern_section import (
    TXCJourneyPatternSectionFactory,
    TXCJourneyPatternStopUsageFactory,
    TXCJourneyPatternTimingLinkFactory,
)


@pytest.mark.parametrize(
    "section,state,context,expected_stops",
    [
        pytest.param(
            TXCJourneyPatternSectionFactory(
                id="1",
                JourneyPatternTimingLink=[
                    TXCJourneyPatternTimingLinkFactory(
                        id="1_1",
                        From=TXCJourneyPatternStopUsageFactory(
                            StopPointRef="2400A001",
                            SequenceNumber="0",
                            TimingStatus="principalTimingPoint",
                        ),
                        To=TXCJourneyPatternStopUsageFactory(
                            StopPointRef="2400A002",
                            SequenceNumber="1",
                            TimingStatus="otherPoint",
                        ),
                        RunTime="PT5M",
                    ),
                ],
            ),
            SectionProcessingState(
                current_time=time(9, 0),
                auto_sequence=0,
                pattern_stops=[],
            ),
            JourneySectionContext(
                service_pattern=TransmodelServicePattern(
                    service_pattern_id="SP1",
                    origin="Origin",
                    destination="Destination",
                    description="123",
                    geom=None,
                    revision_id=123,
                    line_name="test",
                ),
                vehicle_journey=TransmodelVehicleJourney(
                    start_time=time(9, 0),
                    departure_day_shift=False,
                    direction="inbound",
                    journey_code="123",
                    line_ref="123",
                    service_pattern_id=11,
                    block_number="123",
                ),
                txc_vehicle_journey=TXCVehicleJourney(
                    VehicleJourneyCode="VJ1",
                    JourneyPatternRef="JP1",
                    DepartureTime="9:00",
                ),
                pattern_context=GeneratePatternStopsContext(
                    jp_sections=[],
                    stop_sequence=[
                        NaptanStopPointFactory.create(
                            atco_code="2400A001", common_name="First Stop"
                        ),
                        NaptanStopPointFactory.create(
                            atco_code="2400A002", common_name="Second Stop"
                        ),
                    ],
                    activity_map={
                        "pickUpAndSetDown": TransmodelStopActivity(
                            name="pickUpAndSetDown",
                            is_pickup=True,
                            is_setdown=True,
                            is_driverrequest=False,
                        )
                    },
                    naptan_stops_lookup={
                        "2400A001": NaptanStopPointFactory.create(
                            atco_code="2400A001", common_name="First Stop"
                        ),
                        "2400A002": NaptanStopPointFactory.create(
                            atco_code="2400A002", common_name="Second Stop"
                        ),
                    },
                ),
                naptan_stops_lookup={
                    "2400A001": NaptanStopPointFactory.create(
                        atco_code="2400A001", common_name="First Stop"
                    ),
                    "2400A002": NaptanStopPointFactory.create(
                        atco_code="2400A002", common_name="Second Stop"
                    ),
                },
            ),
            [
                {
                    "atco_code": "2400A001",
                    "sequence_number": 0,
                    "departure_time": time(9, 0),
                    "is_timing_point": True,
                },
                {
                    "atco_code": "2400A002",
                    "sequence_number": 1,
                    "departure_time": time(9, 5),
                    "is_timing_point": False,
                },
            ],
            id="Basic single link section with timing",
        ),
        pytest.param(
            TXCJourneyPatternSectionFactory(
                id="1",
                JourneyPatternTimingLink=[
                    TXCJourneyPatternTimingLinkFactory(
                        id="1_1",
                        From=TXCJourneyPatternStopUsageFactory(
                            StopPointRef="2400A001",
                            SequenceNumber="0",
                            TimingStatus="principalTimingPoint",
                            WaitTime="PT2M",
                        ),
                        To=TXCJourneyPatternStopUsageFactory(
                            StopPointRef="2400A002",
                            SequenceNumber="1",
                            TimingStatus="principalTimingPoint",
                        ),
                        RunTime="PT5M",
                    ),
                ],
            ),
            SectionProcessingState(
                current_time=time(9, 0),
                auto_sequence=0,
                pattern_stops=[],
            ),
            JourneySectionContext(
                service_pattern=TransmodelServicePattern(
                    service_pattern_id="SP1",
                    origin="Origin",
                    destination="Destination",
                    description="123",
                    geom=None,
                    revision_id=123,
                    line_name="test",
                ),
                vehicle_journey=TransmodelVehicleJourney(
                    start_time=time(9, 0),
                    departure_day_shift=False,
                    direction="inbound",
                    journey_code="123",
                    line_ref="123",
                    service_pattern_id=11,
                    block_number="123",
                ),
                txc_vehicle_journey=TXCVehicleJourney(
                    VehicleJourneyCode="VJ1",
                    JourneyPatternRef="JP1",
                    DepartureTime="9:00",
                    VehicleJourneyTimingLink=[
                        TXCVehicleJourneyTimingLink(
                            JourneyPatternTimingLinkRef="1_1",
                            RunTime="PT5M",
                            From=TXCVehicleJourneyStopUsageStructure(
                                WaitTime="PT2M",
                            ),
                            To=None,
                        ),
                    ],
                ),
                pattern_context=GeneratePatternStopsContext(
                    jp_sections=[],
                    stop_sequence=[
                        NaptanStopPointFactory.create(
                            atco_code="2400A001", common_name="First Stop"
                        ),
                        NaptanStopPointFactory.create(
                            atco_code="2400A002", common_name="Second Stop"
                        ),
                    ],
                    activity_map={
                        "pickUpAndSetDown": TransmodelStopActivity(
                            name="pickUpAndSetDown",
                            is_pickup=True,
                            is_setdown=True,
                            is_driverrequest=False,
                        )
                    },
                    naptan_stops_lookup={
                        "2400A001": NaptanStopPointFactory.create(
                            atco_code="2400A001", common_name="First Stop"
                        ),
                        "2400A002": NaptanStopPointFactory.create(
                            atco_code="2400A002", common_name="Second Stop"
                        ),
                    },
                ),
                naptan_stops_lookup={
                    "2400A001": NaptanStopPointFactory.create(
                        atco_code="2400A001", common_name="First Stop"
                    ),
                    "2400A002": NaptanStopPointFactory.create(
                        atco_code="2400A002", common_name="Second Stop"
                    ),
                },
            ),
            [
                {
                    "atco_code": "2400A001",
                    "sequence_number": 0,
                    "departure_time": time(9, 0),
                    "is_timing_point": True,
                },
                {
                    "atco_code": "2400A002",
                    "sequence_number": 1,
                    "departure_time": time(9, 7),  # 5 min runtime + 2 min wait
                    "is_timing_point": True,
                },
            ],
            id="Section with wait time",
        ),
    ],
)
def test_process_journey_pattern_section(
    section: TXCJourneyPatternSection,
    state: SectionProcessingState,
    context: JourneySectionContext,
    expected_stops: list[dict],
) -> None:
    """
    Test successful journey pattern section processing.
    """
    success, result_state = process_journey_pattern_section(section, state, context)

    assert success
    assert len(result_state.pattern_stops) == len(expected_stops)
    for actual, expected in zip(result_state.pattern_stops, expected_stops):
        assert actual.atco_code == expected["atco_code"]
        assert actual.sequence_number == expected["sequence_number"]
        assert actual.departure_time == expected["departure_time"]
        assert actual.is_timing_point == expected["is_timing_point"]
