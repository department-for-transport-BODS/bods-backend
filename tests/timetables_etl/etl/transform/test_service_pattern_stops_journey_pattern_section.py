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
from common_layer.xml.txc.models.txc_types import ActivityT
from common_layer.xml.txc.models.txc_vehicle_journey import (
    TXCVehicleJourney,
    TXCVehicleJourneyStopUsageStructure,
    TXCVehicleJourneyTimingLink,
)
from common_layer.xml.txc.parser.vehicle_journeys import (
    parse_vehicle_journey_timing_links,
)
from lxml import etree

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
    generate_pattern_stops,
    process_journey_pattern_section,
)


@pytest.mark.parametrize(
    "activity",
    [
        "pickUpDriverRequest",
        "setDownDriverRequest",
        "pickUpAndSetDownDriverRequest",
        "noPickUpAndSetDown",
    ],
)
@pytest.mark.parametrize("override_endpoint", ["From", "To", "Both"])
@pytest.mark.parametrize("split_sections", [False, True])
def test_activity_overrides_reach_stop_rows(
    journey_context_without_vjtl: JourneySectionContext,
    activity: ActivityT,
    override_endpoint: str,
    split_sections: bool,
) -> None:
    """Keep departure-specific activities, including incoming-only overrides."""
    context = journey_context_without_vjtl
    assert isinstance(context.txc_vehicle_journey, TXCVehicleJourney)
    context.pattern_context.stop_activity_id_map[activity] = 4
    links = [
        TXCJourneyPatternTimingLinkFactory(
            id="activity_1",
            From=TXCJourneyPatternStopUsageFactory(StopPointRef="2400A001"),
            To=TXCJourneyPatternStopUsageFactory(StopPointRef="2400A002"),
            RunTime="PT2M",
        ),
        TXCJourneyPatternTimingLinkFactory(
            id="activity_2",
            From=TXCJourneyPatternStopUsageFactory(StopPointRef="2400A002"),
            To=TXCJourneyPatternStopUsageFactory(StopPointRef="2400A003"),
            RunTime="PT1M",
        ),
    ]
    sections: list[TXCJourneyPatternSection] = (
        [
            TXCJourneyPatternSectionFactory(JourneyPatternTimingLink=[link])
            for link in links
        ]
        if split_sections
        else [TXCJourneyPatternSectionFactory(JourneyPatternTimingLink=links)]
    )
    before = [section.model_dump() for section in sections]
    context.pattern_context.jp_sections = sections
    incoming = (
        f"<To><Activity>{activity}</Activity></To>"
        if override_endpoint in ("To", "Both")
        else ""
    )
    outgoing = (
        f"<From><Activity>{activity}</Activity></From>"
        if override_endpoint in ("From", "Both")
        else ""
    )
    context.txc_vehicle_journey.VehicleJourneyTimingLink = parse_vehicle_journey_timing_links(
        etree.fromstring(f"""
                <VehicleJourney>
                  <VehicleJourneyTimingLink>
                    <JourneyPatternTimingLinkRef>unrelated</JourneyPatternTimingLinkRef>
                    <RunTime>PT0S</RunTime>
                    <From><Activity>pass</Activity></From>
                  </VehicleJourneyTimingLink>
                  <VehicleJourneyTimingLink>
                    <JourneyPatternTimingLinkRef>activity_1</JourneyPatternTimingLinkRef>
                    <RunTime>PT2M</RunTime>
                    <From><Activity>{activity}</Activity></From>
                    {incoming}
                  </VehicleJourneyTimingLink>
                  <VehicleJourneyTimingLink>
                    <JourneyPatternTimingLinkRef>activity_2</JourneyPatternTimingLinkRef>
                    <RunTime>PT1M</RunTime>
                    {outgoing}
                    <To><Activity>{activity}</Activity></To>
                  </VehicleJourneyTimingLink>
                </VehicleJourney>
                """)
    )

    stops = generate_pattern_stops(
        context.service_pattern,
        context.vehicle_journey,
        context.txc_vehicle_journey,
        context.pattern_context,
    )

    assert [stop.stop_activity_id for stop in stops] == [4, 4, 4]
    assert [stop.atco_code for stop in stops] == ["2400A001", "2400A002", "2400A003"]
    assert [stop.departure_time for stop in stops] == [
        time(9, 0),
        time(9, 2),
        time(9, 3),
    ]
    assert [section.model_dump() for section in sections] == before

    context.txc_vehicle_journey.VehicleJourneyTimingLink = []
    other_departure_stops = generate_pattern_stops(
        context.service_pattern,
        context.vehicle_journey,
        context.txc_vehicle_journey,
        context.pattern_context,
    )

    assert [stop.stop_activity_id for stop in other_departure_stops] == [3, 3, 3]


@pytest.mark.parametrize("split_sections", [False, True])
def test_outgoing_activity_overrides_incoming_activity(
    journey_context_without_vjtl: JourneySectionContext,
    split_sections: bool,
) -> None:
    """Use the outgoing From override consistently at shared stops."""
    context = journey_context_without_vjtl
    assert isinstance(context.txc_vehicle_journey, TXCVehicleJourney)
    context.pattern_context.stop_activity_id_map.update(
        {"setDownDriverRequest": 4, "pickUpDriverRequest": 5}
    )
    links = [
        TXCJourneyPatternTimingLinkFactory(
            id="incoming",
            From=TXCJourneyPatternStopUsageFactory(StopPointRef="2400A001"),
            To=TXCJourneyPatternStopUsageFactory(StopPointRef="2400A002"),
        ),
        TXCJourneyPatternTimingLinkFactory(
            id="outgoing",
            From=TXCJourneyPatternStopUsageFactory(StopPointRef="2400A002"),
            To=TXCJourneyPatternStopUsageFactory(StopPointRef="2400A003"),
        ),
    ]
    context.pattern_context.jp_sections = (
        [
            TXCJourneyPatternSectionFactory(JourneyPatternTimingLink=[link])
            for link in links
        ]
        if split_sections
        else [TXCJourneyPatternSectionFactory(JourneyPatternTimingLink=links)]
    )
    context.txc_vehicle_journey.VehicleJourneyTimingLink = [
        TXCVehicleJourneyTimingLink(
            JourneyPatternTimingLinkRef="incoming",
            RunTime="PT0S",
            To=TXCVehicleJourneyStopUsageStructure(Activity="setDownDriverRequest"),
        ),
        TXCVehicleJourneyTimingLink(
            JourneyPatternTimingLinkRef="outgoing",
            RunTime="PT0S",
            From=TXCVehicleJourneyStopUsageStructure(Activity="pickUpDriverRequest"),
        ),
    ]

    stops = generate_pattern_stops(
        context.service_pattern,
        context.vehicle_journey,
        context.txc_vehicle_journey,
        context.pattern_context,
    )

    assert [stop.stop_activity_id for stop in stops] == [3, 5, 3]


def test_missing_activity_override_lookup_fails_explicitly(
    journey_context_without_vjtl: JourneySectionContext,
) -> None:
    """Missing lookup data must not silently drop a stop or its override."""
    context = journey_context_without_vjtl
    assert isinstance(context.txc_vehicle_journey, TXCVehicleJourney)
    section = TXCJourneyPatternSectionFactory(
        JourneyPatternTimingLink=[
            TXCJourneyPatternTimingLinkFactory(
                id="missing_activity",
                From=TXCJourneyPatternStopUsageFactory(StopPointRef="2400A001"),
                To=TXCJourneyPatternStopUsageFactory(StopPointRef="2400A002"),
            )
        ]
    )
    context.txc_vehicle_journey.VehicleJourneyTimingLink = [
        TXCVehicleJourneyTimingLink(
            JourneyPatternTimingLinkRef="missing_activity",
            RunTime="PT0S",
            From=TXCVehicleJourneyStopUsageStructure(Activity="noPickUpAndSetDown"),
        )
    ]
    state = SectionProcessingState(
        current_time=time(9, 0), auto_sequence=0, pattern_stops=[]
    )

    with pytest.raises(ValueError, match="noPickUpAndSetDown"):
        process_journey_pattern_section(section, state, context)


def test_activity_override_does_not_affect_later_visit_to_same_stop(
    journey_context_without_vjtl: JourneySectionContext,
) -> None:
    """Overrides belong to a timing link, not every occurrence of an ATCO code."""
    context = journey_context_without_vjtl
    assert isinstance(context.txc_vehicle_journey, TXCVehicleJourney)
    context.pattern_context.stop_activity_id_map["pickUpDriverRequest"] = 4
    context.pattern_context.jp_sections = [
        TXCJourneyPatternSectionFactory(
            JourneyPatternTimingLink=[
                TXCJourneyPatternTimingLinkFactory(
                    id="first_visit",
                    From=TXCJourneyPatternStopUsageFactory(StopPointRef="2400A001"),
                    To=TXCJourneyPatternStopUsageFactory(StopPointRef="2400A002"),
                ),
                TXCJourneyPatternTimingLinkFactory(
                    id="return_visit",
                    From=TXCJourneyPatternStopUsageFactory(StopPointRef="2400A002"),
                    To=TXCJourneyPatternStopUsageFactory(StopPointRef="2400A001"),
                ),
            ]
        )
    ]
    context.txc_vehicle_journey.VehicleJourneyTimingLink = [
        TXCVehicleJourneyTimingLink(
            JourneyPatternTimingLinkRef="first_visit",
            RunTime="PT0S",
            From=TXCVehicleJourneyStopUsageStructure(Activity="pickUpDriverRequest"),
        )
    ]

    stops = generate_pattern_stops(
        context.service_pattern,
        context.vehicle_journey,
        context.txc_vehicle_journey,
        context.pattern_context,
    )

    assert [stop.atco_code for stop in stops] == ["2400A001", "2400A002", "2400A001"]
    assert [stop.stop_activity_id for stop in stops] == [4, 3, 3]


@pytest.mark.parametrize(
    "incoming_wait,outgoing_wait",
    [
        ("PT19M", "PT19M"),
        ("PT19M", None),
        (None, "PT19M"),
        ("PT19M", "PT0S"),
        ("PT0S", "PT19M"),
    ],
)
@pytest.mark.parametrize("split_sections", [False, True])
@pytest.mark.parametrize("vehicle_waits", [False, True])
def test_wait_is_applied_once_at_its_stop(
    journey_context_without_vjtl: JourneySectionContext,
    incoming_wait: str | None,
    outgoing_wait: str | None,
    split_sections: bool,
    vehicle_waits: bool,
) -> None:
    """Incoming To and outgoing From describe the wait at the same stop."""
    journey_context_without_vjtl.txc_vehicle_journey.VehicleJourneyTimingLink = []
    section = TXCJourneyPatternSectionFactory(
        JourneyPatternTimingLink=[
            TXCJourneyPatternTimingLinkFactory(
                id="wait_1",
                From=TXCJourneyPatternStopUsageFactory(
                    StopPointRef="2400A001", WaitTime=None
                ),
                To=TXCJourneyPatternStopUsageFactory(
                    StopPointRef="2400A002", WaitTime=incoming_wait
                ),
                RunTime="PT2M",
            ),
            TXCJourneyPatternTimingLinkFactory(
                id="wait_2",
                From=TXCJourneyPatternStopUsageFactory(
                    StopPointRef="2400A002", WaitTime=outgoing_wait
                ),
                To=TXCJourneyPatternStopUsageFactory(
                    StopPointRef="2400A003", WaitTime="PT25M"
                ),
                RunTime="PT1M",
            ),
        ]
    )
    if vehicle_waits:
        journey_context_without_vjtl.txc_vehicle_journey.VehicleJourneyTimingLink = [
            TXCVehicleJourneyTimingLink(
                id="override_1",
                JourneyPatternTimingLinkRef="wait_1",
                RunTime="PT2M",
                To=TXCVehicleJourneyStopUsageStructure(WaitTime=incoming_wait),
            ),
            TXCVehicleJourneyTimingLink(
                id="override_2",
                JourneyPatternTimingLinkRef="wait_2",
                RunTime="PT1M",
                From=TXCVehicleJourneyStopUsageStructure(WaitTime=outgoing_wait),
            ),
        ]
        section.JourneyPatternTimingLink[0].To.WaitTime = "PT3M"
        section.JourneyPatternTimingLink[1].From.WaitTime = "PT3M"

    sections = (
        [
            TXCJourneyPatternSectionFactory(JourneyPatternTimingLink=[link])
            for link in section.JourneyPatternTimingLink
        ]
        if split_sections
        else [section]
    )
    state = SectionProcessingState(
        current_time=time(6, 43), auto_sequence=0, pattern_stops=[]
    )
    for current_section in sections:
        success, state = process_journey_pattern_section(
            current_section, state, journey_context_without_vjtl
        )
        assert success

    assert [stop.departure_time for stop in state.pattern_stops] == [
        time(6, 43),
        time(7, 4),
        time(7, 5),
    ]


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
        VehicleJourneyTimingLink=[
            TXCVehicleJourneyTimingLink(
                id="VJTL1",
                JourneyPatternTimingLinkRef="1_1",
                VehicleJourneyRef="VJ1",
                RunTime="PT4M",
                From=TXCVehicleJourneyStopUsageStructure(WaitTime="PT10M"),
                To=TXCVehicleJourneyStopUsageStructure(),
            ),
            TXCVehicleJourneyTimingLink(
                id="VJTL2",
                JourneyPatternTimingLinkRef="1_2",
                VehicleJourneyRef="VJ2",
                RunTime="PT2M",
                From=TXCVehicleJourneyStopUsageStructure(WaitTime="PT5M"),
                To=TXCVehicleJourneyStopUsageStructure(),
            ),
        ],
    )


@pytest.fixture
def txc_vehicle_journey_without_vjtl() -> TXCVehicleJourney:
    """Fixture for a basic TXC Vehicle Journey"""
    return TXCVehicleJourney(
        VehicleJourneyCode="VJ1",
        JourneyPatternRef="JP1",
        DepartureTime="9:00",
        VehicleJourneyTimingLink=[
            TXCVehicleJourneyTimingLink(
                id="VJTL1",
                JourneyPatternTimingLinkRef="1_1",
                VehicleJourneyRef="VJ1",
                RunTime="PT4M",
            ),
            TXCVehicleJourneyTimingLink(
                id="VJTL2",
                JourneyPatternTimingLinkRef="1_2",
                VehicleJourneyRef="VJ2",
                RunTime="PT2M",
            ),
        ],
    )


@pytest.fixture
def naptan_stop_lookup() -> dict[str, NaptanStopPoint]:
    """Fixture for creating a stop lookup dictionary"""
    stops: dict[str, NaptanStopPoint] = {
        "2400A001": NaptanStopPointFactory.create_with_id(
            atco_code="2400A001", common_name="First Stop", id_number=123
        ),
        "2400A002": NaptanStopPointFactory.create_with_id(
            atco_code="2400A002", common_name="Second Stop", id_number=456
        ),
        "2400A003": NaptanStopPointFactory.create_with_id(
            atco_code="2400A003", common_name="Third Stop", id_number=789
        ),
        "2400A004": NaptanStopPointFactory.create_with_id(
            atco_code="2400A004", common_name="Forth Stop", id_number=999
        ),
    }
    return stops


@pytest.fixture
def stop_activity_id_map() -> dict[str, int]:
    """Fixture for stop activities"""
    return {
        "pickUp": 1,
        "setDown": 2,
        "pickUpAndSetDown": 3,
    }


@pytest.fixture
def journey_context(
    service_pattern: TransmodelServicePattern,
    vehicle_journey: TransmodelVehicleJourney,
    txc_vehicle_journey: TXCVehicleJourney,
    naptan_stop_lookup: dict[str, NaptanStopPoint],  # Explicit dictionary type
    stop_activity_id_map: dict[str, int],  # Explicit dictionary type
) -> JourneySectionContext:
    """Fixture for JourneySectionContext"""
    return JourneySectionContext(
        service_pattern=service_pattern,
        vehicle_journey=vehicle_journey,
        txc_vehicle_journey=txc_vehicle_journey,
        pattern_context=GeneratePatternStopsContext(
            jp_sections=[],
            stop_sequence=list(naptan_stop_lookup.values()),
            stop_activity_id_map=stop_activity_id_map,
            naptan_stops_lookup=naptan_stop_lookup,
        ),
        naptan_stops_lookup=naptan_stop_lookup,
    )


@pytest.fixture
def journey_context_without_vjtl(
    service_pattern: TransmodelServicePattern,
    vehicle_journey: TransmodelVehicleJourney,
    txc_vehicle_journey_without_vjtl: TXCVehicleJourney,
    naptan_stop_lookup: dict[str, NaptanStopPoint],  # Explicit dictionary type
    stop_activity_id_map: dict[str, int],  # Explicit dictionary type
) -> JourneySectionContext:
    """Fixture for JourneySectionContext"""
    return JourneySectionContext(
        service_pattern=service_pattern,
        vehicle_journey=vehicle_journey,
        txc_vehicle_journey=txc_vehicle_journey_without_vjtl,
        pattern_context=GeneratePatternStopsContext(
            jp_sections=[],
            stop_sequence=list(naptan_stop_lookup.values()),
            stop_activity_id_map=stop_activity_id_map,
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
                    TXCJourneyPatternTimingLinkFactory(
                        id="1_2",
                        From=TXCJourneyPatternStopUsageFactory(
                            StopPointRef="2400A002",
                            WaitTime="PT13M",
                            SequenceNumber="1",
                            TimingStatus="otherPoint",
                        ),
                        To=TXCJourneyPatternStopUsageFactory(
                            StopPointRef="2400A003",
                            SequenceNumber="2",
                            TimingStatus="otherPoint",
                        ),
                        RunTime="PT2M",
                    ),
                    TXCJourneyPatternTimingLinkFactory(
                        id="1_3",
                        From=TXCJourneyPatternStopUsageFactory(
                            StopPointRef="2400A003",
                            SequenceNumber="2",
                            WaitTime="PT5M",
                            TimingStatus="otherPoint",
                        ),
                        To=TXCJourneyPatternStopUsageFactory(
                            StopPointRef="2400A004",
                            SequenceNumber="3",
                            TimingStatus="otherPoint",
                        ),
                        RunTime="PT3M",
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
                    "naptan_stop_id": 123,
                },
                {
                    "atco_code": "2400A002",
                    "sequence_number": 1,
                    "departure_time": time(9, 17),
                    "is_timing_point": False,
                    "naptan_stop_id": 456,
                },
                {
                    "atco_code": "2400A003",
                    "sequence_number": 2,
                    "departure_time": time(9, 24),
                    "is_timing_point": False,
                    "naptan_stop_id": 789,
                },
                {
                    "atco_code": "2400A004",
                    "sequence_number": 3,
                    "departure_time": time(9, 27),
                    "is_timing_point": False,
                    "naptan_stop_id": 999,
                },
            ],
            id="Basic single link section with no timing",
        ),
    ],
)
def test_process_journey_pattern_section_jptl(
    section: TXCJourneyPatternSection,
    state: SectionProcessingState,
    journey_context_without_vjtl: JourneySectionContext,
    expected_stops: list[dict[str, Any]],
) -> None:
    """
    Test successful journey pattern section processing.
    """
    success, result_state = process_journey_pattern_section(
        section, state, journey_context_without_vjtl
    )

    assert success
    assert len(result_state.pattern_stops) == len(expected_stops)
    for actual, expected in zip(result_state.pattern_stops, expected_stops):
        assert actual.atco_code == expected["atco_code"]
        assert actual.sequence_number == expected["sequence_number"]
        assert actual.departure_time == expected["departure_time"]
        assert actual.is_timing_point == expected["is_timing_point"]
        assert actual.naptan_stop_id == expected["naptan_stop_id"]


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
                            WaitTime="PT13M",
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
                    "departure_time": time(9, 10),
                    "is_timing_point": True,
                    "naptan_stop_id": 123,
                },
                {
                    "atco_code": "2400A002",
                    "sequence_number": 1,
                    "departure_time": time(9, 14),
                    "is_timing_point": False,
                    "naptan_stop_id": 456,
                },
            ],
            id="Basic single link section with no timing",
        ),
    ],
)
def test_process_journey_pattern_section_vjtl(
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
        assert actual.naptan_stop_id == expected["naptan_stop_id"]
