"""
Test Processing Journey Pattern Sections
"""

from datetime import time
from typing import Any

import pytest
from common_layer.database.models.model_naptan import NaptanStopPoint
from common_layer.database.models.model_transmodel import (
    TransmodelServicePattern,
    TransmodelStopActivity,
)
from common_layer.database.models.model_transmodel_vehicle_journey import (
    TransmodelVehicleJourney,
)
from common_layer.xml.txc.models.txc_journey_pattern import TXCJourneyPatternSection
from common_layer.xml.txc.models.txc_vehicle_journey import TXCVehicleJourney

from tests.factories.database.naptan import NaptanStopPointFactory
from tests.timetables_etl.factories.txc.factory_txc_journey_pattern_section import (
    TXCJourneyPatternSectionFactory,
    TXCJourneyPatternStopUsageFactory,
    TXCJourneyPatternTimingLinkFactory,
)
from timetables_etl.etl.app.transform.models_context import (
    GeneratePatternStopsContext,
    JourneySectionContext,
    SectionProcessingState,
)
from timetables_etl.etl.app.transform.service_pattern_stops import (
    process_journey_pattern_section,
)


@pytest.fixture
def service_pattern() -> TransmodelServicePattern:
    """Fixture for a sample Service Pattern"""
    return TransmodelServicePattern(
        service_pattern_id="SP1",
        origin="Origin",
        destination="Destination",
        description="123",
        geom=None,
        revision_id=123,
        line_name="test",
    )


@pytest.fixture
def vehicle_journey() -> TransmodelVehicleJourney:
    """Fixture for a sample Vehicle Journey"""
    return TransmodelVehicleJourney(
        start_time=time(9, 0),
        departure_day_shift=False,
        direction="inbound",
        journey_code="123",
        line_ref="123",
        service_pattern_id=11,
        block_number="123",
    )


@pytest.fixture
def txc_vehicle_journey() -> TXCVehicleJourney:
    """Fixture for a basic TXC Vehicle Journey"""
    return TXCVehicleJourney(
        VehicleJourneyCode="VJ1",
        JourneyPatternRef="JP1",
        DepartureTime="9:00",
    )


@pytest.fixture
def naptan_stop_lookup() -> dict[str, NaptanStopPoint]:
    """Fixture for creating a stop lookup dictionary"""
    stops: dict[str, NaptanStopPoint] = {
        "2400A001": NaptanStopPointFactory.create(
            atco_code="2400A001", common_name="First Stop"
        ),
        "2400A002": NaptanStopPointFactory.create(
            atco_code="2400A002", common_name="Second Stop"
        ),
    }
    return stops


@pytest.fixture
def activity_map() -> dict[str, TransmodelStopActivity]:
    """Fixture for stop activities"""
    return {
        "pickUpAndSetDown": TransmodelStopActivity(
            name="pickUpAndSetDown",
            is_pickup=True,
            is_setdown=True,
            is_driverrequest=False,
        )
    }


@pytest.fixture
def journey_context(
    service_pattern: TransmodelServicePattern,
    vehicle_journey: TransmodelVehicleJourney,
    txc_vehicle_journey: TXCVehicleJourney,
    naptan_stop_lookup: dict[str, NaptanStopPoint],  # Explicit dictionary type
    activity_map: dict[str, TransmodelStopActivity],  # Explicit dictionary type
) -> JourneySectionContext:
    """Fixture for JourneySectionContext"""
    return JourneySectionContext(
        service_pattern=service_pattern,
        vehicle_journey=vehicle_journey,
        txc_vehicle_journey=txc_vehicle_journey,
        pattern_context=GeneratePatternStopsContext(
            jp_sections=[],
            stop_sequence=list(naptan_stop_lookup.values()),
            activity_map=activity_map,
            naptan_stops_lookup=naptan_stop_lookup,
        ),
        naptan_stops_lookup=naptan_stop_lookup,
    )


@pytest.mark.parametrize(
    "section, state, expected_stops",
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
    ],
)
def test_process_journey_pattern_section(
    section: TXCJourneyPatternSection,
    state: SectionProcessingState,
    journey_context: JourneySectionContext,
    expected_stops: list[dict[str, Any]],
) -> None:
    """
    Test successful journey pattern section processing.
    """
    success, result_state = process_journey_pattern_section(
        section, state, journey_context
    )

    assert success
    assert len(result_state.pattern_stops) == len(expected_stops)
    for actual, expected in zip(result_state.pattern_stops, expected_stops):
        assert actual.atco_code == expected["atco_code"]
        assert actual.sequence_number == expected["sequence_number"]
        assert actual.departure_time == expected["departure_time"]
        assert actual.is_timing_point == expected["is_timing_point"]
