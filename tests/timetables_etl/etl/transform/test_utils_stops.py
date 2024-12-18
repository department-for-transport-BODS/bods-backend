"""
Test Stop Handling Utils
"""

import pytest
from common_layer.txc.models import (
    TXCJourneyPattern,
    TXCJourneyPatternSection,
    TXCJourneyPatternStopUsage,
    TXCJourneyPatternTimingLink,
)

from tests.timetables_etl.factories.database.naptan import NaptanStopPointFactory
from timetables_etl.etl.app.transform.utils_stops import (
    get_first_last_stops,
    get_terminal_stop_points,
)

STOP_MAPPING_DATA = [
    ("490014051VC", "Victoria Coach Station"),
    ("118000037", "Plymouth Coach Station"),
    ("43002103108", "Birmingham Coach Station"),
    ("1600ZZGRCRC0", "Cheltenham Racecourse"),
    ("2000G008000", "Three Pears"),
]


@pytest.mark.parametrize(
    "journey_pattern,sections,expected_terminal_stops",
    [
        pytest.param(
            TXCJourneyPattern(
                id="JP1",
                DestinationDisplay="Victoria - Plymouth",
                Direction="inbound",
                RouteRef="R1",
                JourneyPatternSectionRefs=["JPS1"],
            ),
            [
                TXCJourneyPatternSection(
                    id="JPS1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLink(
                            id="JPTL1",
                            From=TXCJourneyPatternStopUsage(
                                id="JPSU1",
                                SequenceNumber=None,
                                WaitTime=None,
                                Activity="pickUp",
                                DynamicDestinationDisplay=None,
                                Notes=None,
                                StopPointRef="490014051VC",
                                TimingStatus="principalTimingPoint",
                                FareStageNumber=None,
                                FareStage=None,
                            ),
                            To=TXCJourneyPatternStopUsage(
                                id="JPSU2",
                                SequenceNumber=None,
                                WaitTime=None,
                                Activity="pickUpAndSetDown",
                                DynamicDestinationDisplay=None,
                                Notes=None,
                                StopPointRef="035059860001",
                                TimingStatus="principalTimingPoint",
                                FareStageNumber=None,
                                FareStage=None,
                            ),
                            RouteLinkRef="RL1",
                            RunTime="PT0H0M0S",
                            Distance=None,
                        ),
                        TXCJourneyPatternTimingLink(
                            id="JPTL2",
                            From=TXCJourneyPatternStopUsage(
                                id="JPSU3",
                                SequenceNumber=None,
                                WaitTime="PT0H5M0S",
                                Activity="pickUpAndSetDown",
                                DynamicDestinationDisplay=None,
                                Notes=None,
                                StopPointRef="035059860001",
                                TimingStatus="principalTimingPoint",
                                FareStageNumber=None,
                                FareStage=None,
                            ),
                            To=TXCJourneyPatternStopUsage(
                                id="JPSU4",
                                SequenceNumber=None,
                                WaitTime=None,
                                Activity="pickUpAndSetDown",
                                DynamicDestinationDisplay=None,
                                Notes=None,
                                StopPointRef="01000053216",
                                TimingStatus="principalTimingPoint",
                                FareStageNumber=None,
                                FareStage=None,
                            ),
                            RouteLinkRef="RL2",
                            RunTime="PT0H0M0S",
                            Distance=None,
                        ),
                        TXCJourneyPatternTimingLink(
                            id="JPTL3",
                            From=TXCJourneyPatternStopUsage(
                                id="JPSU5",
                                SequenceNumber=None,
                                WaitTime="PT0H10M0S",
                                Activity="pickUpAndSetDown",
                                DynamicDestinationDisplay=None,
                                Notes=None,
                                StopPointRef="01000053216",
                                TimingStatus="principalTimingPoint",
                                FareStageNumber=None,
                                FareStage=None,
                            ),
                            To=TXCJourneyPatternStopUsage(
                                id="JPSU6",
                                SequenceNumber=None,
                                WaitTime=None,
                                Activity="pickUpAndSetDown",
                                DynamicDestinationDisplay=None,
                                Notes=None,
                                StopPointRef="360000174",
                                TimingStatus="principalTimingPoint",
                                FareStageNumber=None,
                                FareStage=None,
                            ),
                            RouteLinkRef="RL3",
                            RunTime="PT0H0M0S",
                            Distance=None,
                        ),
                        TXCJourneyPatternTimingLink(
                            id="JPTL4",
                            From=TXCJourneyPatternStopUsage(
                                id="JPSU7",
                                SequenceNumber=None,
                                WaitTime="PT0H5M0S",
                                Activity="pickUpAndSetDown",
                                DynamicDestinationDisplay=None,
                                Notes=None,
                                StopPointRef="360000174",
                                TimingStatus="principalTimingPoint",
                                FareStageNumber=None,
                                FareStage=None,
                            ),
                            To=TXCJourneyPatternStopUsage(
                                id="JPSU8",
                                SequenceNumber=None,
                                WaitTime=None,
                                Activity="pickUpAndSetDown",
                                DynamicDestinationDisplay=None,
                                Notes=None,
                                StopPointRef="1100DEA57098",
                                TimingStatus="principalTimingPoint",
                                FareStageNumber=None,
                                FareStage=None,
                            ),
                            RouteLinkRef="RL4",
                            RunTime="PT0H0M0S",
                            Distance=None,
                        ),
                        TXCJourneyPatternTimingLink(
                            id="JPTL5",
                            From=TXCJourneyPatternStopUsage(
                                id="JPSU9",
                                SequenceNumber=None,
                                WaitTime="PT0H5M0S",
                                Activity="pickUpAndSetDown",
                                DynamicDestinationDisplay=None,
                                Notes=None,
                                StopPointRef="1100DEA57098",
                                TimingStatus="principalTimingPoint",
                                FareStageNumber=None,
                                FareStage=None,
                            ),
                            To=TXCJourneyPatternStopUsage(
                                id="JPSU10",
                                SequenceNumber=None,
                                WaitTime=None,
                                Activity="setDown",
                                DynamicDestinationDisplay=None,
                                Notes=None,
                                StopPointRef="118000037",
                                TimingStatus="principalTimingPoint",
                                FareStageNumber=None,
                                FareStage=None,
                            ),
                            RouteLinkRef="RL5",
                            RunTime="PT0H0M0S",
                            Distance=None,
                        ),
                    ],
                )
            ],
            ("490014051VC", "118000037"),
            id="Single Journey Pattern Section",
        ),
        pytest.param(
            TXCJourneyPattern(
                id="JP2",
                DestinationDisplay="Digbeth, Birmingham - Cheltenham",
                Direction="outbound",
                RouteRef="R2",
                JourneyPatternSectionRefs=["JPS2", "JPS3"],
            ),
            [
                TXCJourneyPatternSection(
                    id="JPS2",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLink(
                            id="JPTL8",
                            From=TXCJourneyPatternStopUsage(
                                id="JPSU13",
                                SequenceNumber=None,
                                WaitTime=None,
                                Activity="pickUp",
                                DynamicDestinationDisplay=None,
                                Notes=None,
                                StopPointRef="43002103108",
                                TimingStatus="principalTimingPoint",
                                FareStageNumber=None,
                                FareStage=None,
                            ),
                            To=TXCJourneyPatternStopUsage(
                                id="JPSU14",
                                SequenceNumber=None,
                                WaitTime=None,
                                Activity="pickUpAndSetDown",
                                DynamicDestinationDisplay=None,
                                Notes=None,
                                StopPointRef="1600ZZGRCRC0",
                                TimingStatus="principalTimingPoint",
                                FareStageNumber=None,
                                FareStage=None,
                            ),
                            RouteLinkRef="RL7",
                            RunTime="PT0H0M0S",
                            Distance=None,
                        ),
                    ],
                ),
                TXCJourneyPatternSection(
                    id="JPS3",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLink(
                            id="JPTL9",
                            From=TXCJourneyPatternStopUsage(
                                id="JPSU15",
                                SequenceNumber=None,
                                WaitTime=None,
                                Activity="pickUpAndSetDown",
                                DynamicDestinationDisplay=None,
                                Notes=None,
                                StopPointRef="1600ZZGRCRC0",
                                TimingStatus="principalTimingPoint",
                                FareStageNumber=None,
                                FareStage=None,
                            ),
                            To=TXCJourneyPatternStopUsage(
                                id="JPSU16",
                                SequenceNumber=None,
                                WaitTime=None,
                                Activity="setDown",
                                DynamicDestinationDisplay=None,
                                Notes=None,
                                StopPointRef="2000G008000",
                                TimingStatus="principalTimingPoint",
                                FareStageNumber=None,
                                FareStage=None,
                            ),
                            RouteLinkRef="RL8",
                            RunTime="PT0H0M0S",
                            Distance=None,
                        ),
                    ],
                ),
            ],
            ("43002103108", "2000G008000"),
            id="Multiple Journey Pattern Sections",
        ),
    ],
)
class TestTerminalStops:
    """
    Test finding first and last stop functions
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Pytest doesn't accept classes with init methods
        """
        self.stop_mapping = NaptanStopPointFactory.create_mapping(STOP_MAPPING_DATA)

    def test_get_terminal_stop_points(
        self,
        journey_pattern: TXCJourneyPattern,
        sections: list[TXCJourneyPatternSection],
        expected_terminal_stops: tuple[str, str],
    ):
        """
        Test getting the Naptan Data for first and last
        """
        first_stop, last_stop = get_terminal_stop_points(
            journey_pattern, sections, self.stop_mapping
        )
        assert first_stop.atco_code == expected_terminal_stops[0]
        assert last_stop.atco_code == expected_terminal_stops[1]

    def test_get_first_last_stops(
        self,
        journey_pattern: TXCJourneyPattern,
        sections: list[TXCJourneyPatternSection],
        expected_terminal_stops: tuple[str, str],
    ):
        """
        Test returning common name tuple for first and last
        """
        result = get_first_last_stops(journey_pattern, sections, self.stop_mapping)
        expected_names = (
            self.stop_mapping[expected_terminal_stops[0]].common_name,
            self.stop_mapping[expected_terminal_stops[1]].common_name,
        )
        assert result == expected_names
