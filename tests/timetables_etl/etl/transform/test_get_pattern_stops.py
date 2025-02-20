"""
Tests to ensure we get the right stop order
"""

import pytest
from common_layer.xml.txc.models.txc_journey_pattern import TXCJourneyPatternSection
from common_layer.xml.txc.models.txc_service import TXCJourneyPattern

from src.timetables_etl.etl.app.helpers.dataclasses.stop_points import (
    NonExistentNaptanStop,
)
from src.timetables_etl.etl.app.helpers.types import StopsLookup
from src.timetables_etl.etl.app.transform.utils_stops import get_pattern_stops
from tests.factories.database.naptan import NaptanStopPointFactory
from tests.timetables_etl.factories.txc.factory_txc_journey_pattern_section import (
    TXCJourneyPatternSectionFactory,
    TXCJourneyPatternStopUsageFactory,
    TXCJourneyPatternTimingLinkFactory,
)


@pytest.mark.parametrize(
    "sections,stop_mapping,expected_stops",
    [
        pytest.param(
            [
                TXCJourneyPatternSectionFactory(
                    id="1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLinkFactory(
                            From=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A001",
                                SequenceNumber="0",
                            ),
                            To=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A002",
                                SequenceNumber="1",
                            ),
                        ),
                    ],
                )
            ],
            NaptanStopPointFactory.create_mapping(
                [
                    ("2400A001", "First Stop"),
                    ("2400A002", "Second Stop"),
                ]
            ),
            ["2400A001", "2400A002"],  # Simple sequence
            id="Single section with two stops",
        ),
        pytest.param(
            [
                TXCJourneyPatternSectionFactory(
                    id="1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLinkFactory(
                            From=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A001",
                                SequenceNumber="0",
                            ),
                            To=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A002",
                                SequenceNumber="1",
                            ),
                        ),
                    ],
                ),
                TXCJourneyPatternSectionFactory(
                    id="2",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLinkFactory(
                            From=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A002",  # Boundary stop
                                SequenceNumber="1",
                            ),
                            To=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A003",
                                SequenceNumber="2",
                            ),
                        ),
                    ],
                ),
            ],
            NaptanStopPointFactory.create_mapping(
                [
                    ("2400A001", "First Stop"),
                    ("2400A002", "Middle Stop"),
                    ("2400A003", "Last Stop"),
                ]
            ),
            ["2400A001", "2400A002", "2400A003"],  # No duplication at boundary
            id="Two sections with connecting stop",
        ),
        pytest.param(
            [
                TXCJourneyPatternSectionFactory(
                    id="1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLinkFactory(
                            From=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A001",
                                SequenceNumber="0",
                            ),
                            To=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A002",
                                SequenceNumber="1",
                            ),
                        ),
                        TXCJourneyPatternTimingLinkFactory(
                            From=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A002",
                                SequenceNumber="1",
                            ),
                            To=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A003",
                                SequenceNumber="2",
                            ),
                        ),
                    ],
                )
            ],
            NaptanStopPointFactory.create_mapping(
                [
                    ("2400A001", "First Stop"),
                    ("2400A002", "Middle Stop"),
                    ("2400A003", "Last Stop"),
                ]
            ),
            ["2400A001", "2400A002", "2400A003"],  # Continuous sequence
            id="Single section with multiple links",
        ),
        pytest.param(  # NonExistentNaptanStop test
            [
                TXCJourneyPatternSectionFactory(
                    id="1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLinkFactory(
                            From=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A001",
                                SequenceNumber="0",
                            ),
                            To=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400AMISSING",
                                SequenceNumber="1",
                            ),
                        ),
                    ],
                )
            ],
            {
                "2400A001": NaptanStopPointFactory.create(
                    atco_code="2400A001", common_name="First Stop"
                ),
                "2400AMISSING": NonExistentNaptanStop(
                    atco_code="2400AMISSING", common_name="Missing Stop"
                ),
            },
            ["2400A001"],  # Should skip the NonExistentNaptanStop
            id="Section with non-existent stop",
        ),
        pytest.param(
            [
                TXCJourneyPatternSectionFactory(
                    id="1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLinkFactory(
                            From=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A001",
                                SequenceNumber="0",
                            ),
                            To=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A002",
                                SequenceNumber="1",
                            ),
                        ),
                    ],
                ),
                TXCJourneyPatternSectionFactory(
                    id="2",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLinkFactory(
                            From=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A002",  # Same as previous section's end
                                SequenceNumber="1",
                            ),
                            To=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A003",
                                SequenceNumber="2",
                            ),
                        ),
                    ],
                ),
                TXCJourneyPatternSectionFactory(
                    id="3",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLinkFactory(
                            From=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A003",  # Same as previous section's end
                                SequenceNumber="2",
                            ),
                            To=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A004",
                                SequenceNumber="3",
                            ),
                        ),
                    ],
                ),
            ],
            NaptanStopPointFactory.create_mapping(
                [
                    ("2400A001", "First Stop"),
                    ("2400A002", "Second Stop"),
                    ("2400A003", "Third Stop"),
                    ("2400A004", "Fourth Stop"),
                ]
            ),
            [
                "2400A001",
                "2400A002",
                "2400A003",
                "2400A004",
            ],  # The actual sequence we want
            id="Three connected sections should not duplicate stops",
        ),
        pytest.param(
            [
                TXCJourneyPatternSectionFactory(
                    id="1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLinkFactory(
                            From=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A001",
                                SequenceNumber="0",
                            ),
                            To=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A002",
                                SequenceNumber="1",
                            ),
                        ),
                    ],
                ),
                TXCJourneyPatternSectionFactory(
                    id="2",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLinkFactory(
                            From=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A002",  # Boundary with section 1
                                SequenceNumber="1",
                            ),
                            To=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A001",  # Circular back to first stop
                                SequenceNumber="2",
                            ),
                        ),
                    ],
                ),
                TXCJourneyPatternSectionFactory(
                    id="3",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLinkFactory(
                            From=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A001",  # Boundary with section 2
                                SequenceNumber="2",
                            ),
                            To=TXCJourneyPatternStopUsageFactory(
                                StopPointRef="2400A003",  # Continue to new stop
                                SequenceNumber="3",
                            ),
                        ),
                    ],
                ),
            ],
            NaptanStopPointFactory.create_mapping(
                [
                    ("2400A001", "First/Circle Stop"),
                    ("2400A002", "Second Stop"),
                    ("2400A003", "Final Stop"),
                ]
            ),
            # Should keep the circular occurrence of 2400A001 but remove section boundary duplicate
            ["2400A001", "2400A002", "2400A001", "2400A003"],
            id="Circular route with section boundaries",
        ),
    ],
)
def test_get_pattern_stops(
    sections: list[TXCJourneyPatternSection],
    stop_mapping: StopsLookup,
    expected_stops: list[str],
) -> None:
    """
    Test extraction of stop sequences from journey pattern sections including:
    """
    jp = TXCJourneyPattern(
        id="test_pattern",
        RouteRef="3",
        DestinationDisplay="Test Destination",
        Direction="outbound",
        JourneyPatternSectionRefs=[section.id for section in sections],
    )

    stops = get_pattern_stops(jp, sections, stop_mapping)

    # Check stop sequence matches expected
    assert [stop.atco_code for stop in stops] == expected_stops
