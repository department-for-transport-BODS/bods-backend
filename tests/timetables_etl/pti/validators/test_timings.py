import pytest

from pti.constants import PTI_SCHEMA_PATH
from pti.models import Schema
from pti.validators.pti import PTIValidator

from tests.timetables_etl.pti.validators.conftest import JSONFile, TXCFile
from tests.timetables_etl.pti.validators.factories import SchemaFactory


@pytest.mark.parametrize(
    ("run_time", "jptl_ref", "has_to_from", "expected"),
    [
        ("PT3M", "JPTL1", False, True),
        ("PT3M", "JPTL1", True, False),
        ("PT3M", "JPTL2", True, True),
        ("PT3M", "JPTL2", False, True),
        ("", "JPTL1", True, True),
        ("PT0M", "JPTL1", True, True),
        ("PT0S", "JPTL1", True, True),
        ("PT0H0M0S", "JPTL1", True, True),
        ("PT1H0M0S", "JPTL1", True, False),
    ],
)
def test_run_time_validation(run_time, jptl_ref, has_to_from, expected):
    """
    Check if a JourneyPatternTimingLink has a non-zero RunTime and it is referenced
    in a VehicleJourneyTimingLink then the parent VehicleJourney should not have
    To/From elements.

    Examples:

    JPTL1 in VJ1 with RunTime PT3M and To/From present -> False
    JPTL1 in VJ1 with RunTime PT3M and To/From absent -> True
    JPTL2 not in VJ1 with RunTime PT3 and To/From present -> True
    JPTL1 in VJ1 with RunTime PT0M and To/From present -> True
    JPTL1 in VJ1 with RunTime PT0H0M0S and To/From present -> True
    JPTL1 in VJ1 with RunTime PT1H0M0S and To/From present -> False
    """
    if run_time:
        run_time = "<RunTime>{0}</RunTime>".format(run_time)

    if jptl_ref:
        jptl_ref = (
            "<JourneyPatternTimingLinkRef>{0}</JourneyPatternTimingLinkRef>".format(
                jptl_ref
            )
        )

    if has_to_from:
        to_from = """
        <From>
            <StopPointRef>9990000001</StopPointRef>
            <TimingStatus>PTP</TimingStatus>
        </From>
        <To>
            <StopPointRef>9990000002</StopPointRef>
            <TimingStatus>PTP</TimingStatus>
        </To>
        """
    else:
        to_from = ""

    xml = """
    <JourneyPatternSections>
        <JourneyPatternSection id="JPS1">
            <JourneyPatternTimingLink id="JPTL1">
                <Direction>clockwise</Direction>
                {0}
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
                {1}
                {2}
            </VehicleJourneyTimingLink>
        </VehicleJourney>
    </VehicleJourneys>
    """
    xml = xml.format(run_time, jptl_ref, to_from)

    OBSERVATION_ID = 34
    schema = Schema.from_path(PTI_SCHEMA_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected
