import pytest

from pti.constants import PTI_SCHEMA_PATH
from pti_common.models import Schema
from pti.validators.pti import PTIValidator

from tests.timetables_etl.pti.validators.conftest import JSONFile, TXCFile
from tests.timetables_etl.pti.validators.factories import SchemaFactory


@pytest.mark.parametrize(
    ("refs", "expected"),
    [
        (["9001", "9001", "9002", "9002"], True),
        (["9001", "9002", "9004", "9005"], False),
    ],
)
def test_timing_link_validation(refs, expected):
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
    OBSERVATION_ID = 37
    schema = Schema.from_path(PTI_SCHEMA_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("from_seq", "to_seq", "expected"),
    [
        ('SequenceNumber="1"', 'SequenceNumber="1"', True),
        ("", 'SequenceNumber="1"', False),
        ('SequenceNumber="1"', "", False),
        ("", "", False),
    ],
)
def test_from_has_sequence_number_true(from_seq, to_seq, expected):
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
    OBSERVATION_ID = 38
    schema = Schema.from_path(PTI_SCHEMA_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


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
        jptl_ref = "<JourneyPatternTimingLinkRef>{0}</JourneyPatternTimingLinkRef>".format(jptl_ref)

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
