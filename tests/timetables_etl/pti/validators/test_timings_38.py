"""
Test Timings Observation 38
Mandatory elements incorrect in 'JourneyPatternTimingLink' field.
"""

from pathlib import Path

import pytest

from tests.timetables_etl.pti.validators.conftest import TXCFile, create_validator

DATA_DIR = Path(__file__).parent / "data/journey_patterns"
OBSERVATION_ID = 38


@pytest.mark.parametrize(
    "from_seq, to_seq, expected",
    [
        pytest.param(
            'SequenceNumber="1"',
            'SequenceNumber="1"',
            True,
            id="Both From And To Have Sequence Numbers",
        ),
        pytest.param("", 'SequenceNumber="1"', False, id="Only To Has Sequence Number"),
        pytest.param(
            'SequenceNumber="1"', "", False, id="Only From Has Sequence Number"
        ),
        pytest.param("", "", False, id="Neither From Nor To Have Sequence Numbers"),
    ],
)
def test_timing_link_sequence_numbers(from_seq: str, to_seq: str, expected: bool):
    """
    Test validation of sequence numbers in journey pattern timing links
    Validates that From and To elements have proper sequence numbers
    """
    timing_link = """
   <JourneyPatternTimingLink id="JPTL1">
       <DutyCrewCode>CRW1</DutyCrewCode>
       <From {0}>
           <DynamicDestinationDisplay>Hospital</DynamicDestinationDisplay>
           <StopPointRef>9990000001</StopPointRef>
           <TimingStatus>PTP</TimingStatus>
           <FareStageNumber>001</FareStageNumber>
           <FareStage>true</FareStage>
       </From>
       <To {1}>
           <StopPointRef>9990000002</StopPointRef>
           <TimingStatus>PTP</TimingStatus>
       </To>
       <RouteLinkRef>RL1</RouteLinkRef>
       <Direction>clockwise</Direction>
       <RunTime>PT3M</RunTime>
   </JourneyPatternTimingLink>
   """
    xml = timing_link.format(from_seq, to_seq)
    pti, _ = create_validator("dummy.xml", DATA_DIR, OBSERVATION_ID)
    is_valid = pti.is_valid(TXCFile(xml))
    assert is_valid == expected
