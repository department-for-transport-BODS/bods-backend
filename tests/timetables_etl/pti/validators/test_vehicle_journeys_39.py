"""
Test Vehicle Journeys Observation 39
Mandatory elements incorrect in VehicleJourney field
"""

from pathlib import Path

import pytest

from .conftest import TXCFile, create_validator

DATA_DIR = Path(__file__).parent / "data/vehicle_journeys"
OBSERVATION_ID = 39


@pytest.mark.parametrize(
    "has_vj_ref, has_profile, expected",
    [
        pytest.param(True, False, True, id="Has Vehicle Journey Ref Only"),
        pytest.param(False, False, True, id="No Vehicle Journey Ref Or Profile"),
        pytest.param(False, True, True, id="Has Operating Profile Only"),
        pytest.param(True, True, False, id="Has Both Vehicle Journey Ref And Profile"),
    ],
)
def test_validate_vehicle_journey_ref(
    has_vj_ref: bool, has_profile: bool, expected: bool
):
    """Test validation of vehicle journey references and operating profiles"""
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

    vj_ref = "<VehicleJourneyRef>VJ1</VehicleJourneyRef>" if has_vj_ref else ""
    profile = (
        """
       <OperatingProfile>
           <RegularDayType>
               <DaysOfWeek>
                   <MondayToFriday/>
               </DaysOfWeek>
           </RegularDayType>
       </OperatingProfile>
       """
        if has_profile
        else ""
    )

    xml = vehicle_journey.format(vj_ref, profile)
    pti, _ = create_validator("dummy.xml", DATA_DIR, OBSERVATION_ID)
    is_valid = pti.is_valid(TXCFile(xml))
    assert is_valid == expected
