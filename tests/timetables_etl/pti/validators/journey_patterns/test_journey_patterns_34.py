"""
Test Timings Observation 34
Mandatory elements incorrect in 'JourneyPatternSection' field.
"""

import pytest

from tests.timetables_etl.pti.validators.conftest import TXCFile, create_validator

OBSERVATION_ID = 34


@pytest.mark.parametrize(
    "run_time, jptl_ref, has_to_from, expected",
    [
        pytest.param(
            "PT3M", "JPTL1", False, True, id="Valid - RunTime With No To/From Elements"
        ),
        pytest.param(
            "PT3M", "JPTL1", True, False, id="Invalid - RunTime With To/From Elements"
        ),
        pytest.param(
            "PT3M",
            "JPTL2",
            True,
            True,
            id="Valid - Different JPTL With To/From Elements",
        ),
        pytest.param(
            "PT3M",
            "JPTL2",
            False,
            True,
            id="Valid - Different JPTL Without To/From Elements",
        ),
        pytest.param(
            "", "JPTL1", True, True, id="Valid - No RunTime With To/From Elements"
        ),
        pytest.param(
            "PT0M", "JPTL1", True, True, id="Valid - Zero Minutes With To/From Elements"
        ),
        pytest.param(
            "PT0S", "JPTL1", True, True, id="Valid - Zero Seconds With To/From Elements"
        ),
        pytest.param(
            "PT0H0M0S", "JPTL1", True, True, id="Valid - Zero HMS With To/From Elements"
        ),
        pytest.param(
            "PT1H0M0S",
            "JPTL1",
            True,
            False,
            id="Invalid - One Hour With To/From Elements",
        ),
    ],
)
def test_run_time_validation(
    run_time: str, jptl_ref: str, has_to_from: bool, expected: bool
):
    """
    Check if a JourneyPatternTimingLink has a non-zero RunTime and it is referenced
    in a VehicleJourneyTimingLink then the parent VehicleJourney should not have
    To/From elements.

    Test cases:
    - JPTL1 in VJ1 with RunTime PT3M and To/From present -> False
    - JPTL1 in VJ1 with RunTime PT3M and To/From absent -> True
    - JPTL2 not in VJ1 with RunTime PT3 and To/From present -> True
    - JPTL1 in VJ1 with RunTime PT0M and To/From present -> True
    - JPTL1 in VJ1 with RunTime PT0H0M0S and To/From present -> True
    - JPTL1 in VJ1 with RunTime PT1H0M0S and To/From present -> False
    """
    if run_time:
        run_time = f"<RunTime>{run_time}</RunTime>"

    if jptl_ref:
        jptl_ref = (
            f"<JourneyPatternTimingLinkRef>{jptl_ref}</JourneyPatternTimingLinkRef>"
        )

    to_from = (
        """
       <From>
           <StopPointRef>9990000001</StopPointRef>
           <TimingStatus>PTP</TimingStatus>
       </From>
       <To>
           <StopPointRef>9990000002</StopPointRef>
           <TimingStatus>PTP</TimingStatus>
       </To>
       """
        if has_to_from
        else ""
    )

    xml = f"""
   <JourneyPatternSections>
       <JourneyPatternSection id="JPS1">
           <JourneyPatternTimingLink id="JPTL1">
               <Direction>clockwise</Direction>
               {run_time}
           </JourneyPatternTimingLink>
       </JourneyPatternSection>
   </JourneyPatternSections>
   <VehicleJourneys>
       <VehicleJourney>
           <VehicleJourneyCode>VJ1</VehicleJourneyCode>
           <ServiceRef>S1</ServiceRef>
           <LineRef>L1</LineRef>
           <JourneyPatternRef>JP1</JourneyPatternRef>
           <DepartureTime>10:29:00</DepartureTime>
           <VehicleJourneyTimingLink id="VJTL5">
               {jptl_ref}
               {to_from}
           </VehicleJourneyTimingLink>
       </VehicleJourney>
   </VehicleJourneys>
   """

    pti = create_validator(None, None, OBSERVATION_ID)
    is_valid = pti.is_valid(TXCFile(xml))
    assert is_valid == expected
