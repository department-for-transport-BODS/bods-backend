"""
Test Timings Observation 37
Mandatory elements incorrect in 'JourneyPattern' field
"""

from pathlib import Path

import pytest

from tests.timetables_etl.pti.validators.conftest import TXCFile, create_validator

DATA_DIR = Path(__file__).parent / "data/journey_patterns"
OBSERVATION_ID = 37


@pytest.mark.parametrize(
    "refs, expected",
    [
        pytest.param(
            ["9001", "9001", "9002", "9002"], True, id="Valid Connected Timing Links"
        ),
        pytest.param(
            ["9001", "9002", "9004", "9005"],
            False,
            id="Invalid Disconnected Timing Links",
        ),
    ],
)
def test_timing_link_validation(refs: list[str], expected: bool):
    """
    Test validation of journey pattern timing links
    Validates that consecutive timing links are properly connected
    """
    timing_links = """
   <JourneyPatternSection>
       <JourneyPatternTimingLink id="JPTL1">
           <To>
               <StopPointRef>{0}</StopPointRef>
           </To>
       </JourneyPatternTimingLink>
       <JourneyPatternTimingLink id="JPTL2">
           <From>
               <StopPointRef>{1}</StopPointRef>
           </From>
           <To>
               <StopPointRef>{2}</StopPointRef>
           </To>
       </JourneyPatternTimingLink>
       <JourneyPatternTimingLink id="JPTL3">
           <From>
               <StopPointRef>{3}</StopPointRef>
           </From>
       </JourneyPatternTimingLink>
   </JourneyPatternSection>
   """
    xml = timing_links.format(*refs)
    pti, _ = create_validator("dummy.xml", DATA_DIR, OBSERVATION_ID)
    is_valid = pti.is_valid(TXCFile(xml))
    assert is_valid == expected
