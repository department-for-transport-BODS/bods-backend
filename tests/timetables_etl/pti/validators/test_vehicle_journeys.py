from pathlib import Path

import pytest
from pti.constants import PTI_SCHEMA_PATH
from pti_common.models import Schema
from pti.validators.pti import PTIValidator

from tests.timetables_etl.pti.validators.conftest import JSONFile, TXCFile
from tests.timetables_etl.pti.validators.factories import SchemaFactory

DATA_DIR = Path(__file__).parent / "data/vehicle_journeys"


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("destinationdisplayjourneypattern.xml", True),
        ("dynamicdisplaytiminglinks.xml", True),
        ("dynamicdisplaytiminglinksfail.xml", False),
    ],
)
def test_destination_display(filename, expected):
    OBSERVATION_ID = 47
    schema = Schema.from_path(PTI_SCHEMA_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    txc_path = DATA_DIR / filename

    with txc_path.open("r") as txc:
        is_valid = pti.is_valid(txc)
    assert is_valid == expected

@pytest.mark.parametrize(
    ("has_vj_ref", "has_profile", "expected"),
    [
        (True, False, True),
        (False, False, True),
        (False, True, True),
        (True, True, False),
    ],
)
def test_validate_vehicle_journey_ref(has_vj_ref, has_profile, expected):
    vehicle_journey = """
    <VehicleJourneys>
        <VehicleJourney>
            {0}
            <LineRef>L1</LineRef>
            <ServiceRef>S1</ServiceRef>
            <GarageRef>1</GarageRef>
            {1}
        </VehicleJourney>
    </VehicleJourneys>
    """

    vj_ref = ""
    if has_vj_ref:
        vj_ref = "<VehicleJourneyRef>VJ1</VehicleJourneyRef>"

    profile = ""
    if has_profile:
        profile = """
        <OperatingProfile>
            <RegularDayType>
                <DaysOfWeek>
                    <MondayToFriday/>
                </DaysOfWeek>
            </RegularDayType>
        </OperatingProfile>
        """

    xml = vehicle_journey.format(vj_ref, profile)
    OBSERVATION_ID = 39
    schema = Schema.from_path(PTI_SCHEMA_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected