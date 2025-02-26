"""
Test Services Observation 21
Mandatory element incorrect in 'StandardService' field.
"""

import pytest

from tests.timetables_etl.pti.validators.conftest import TXCFile, create_validator

OBSERVATION_ID = 21


@pytest.mark.parametrize(
    "journey_ids, expected",
    [
        pytest.param(["JP1", "JP2"], True, id="Valid Multiple Journey Patterns"),
        pytest.param(["JP2"], True, id="Valid Single Journey Pattern"),
        pytest.param([], False, id="Invalid No Journey Patterns"),
    ],
)
def test_service_has_journey_pattern(journey_ids: list[str], expected: bool):
    """
    Test validation of journey patterns in a service
    Validates that services have at least one journey pattern
    """
    pattern_template = """
   <JourneyPattern id="{0}">
       <Direction>outbound</Direction>
       <RouteRef>R2</RouteRef>
       <JourneyPatternSectionRefs>JPS1</JourneyPatternSectionRefs>
       <JourneyPatternSectionRefs>JPS3</JourneyPatternSectionRefs>
   </JourneyPattern>
   """

    patterns = "\n".join(pattern_template.format(id_) for id_ in journey_ids)
    service_template = """
   <Services>
       <Service>
           <ServiceCode>1</ServiceCode>
       </Service>
       <StandardService>
           <Origin>Bus Station</Origin>
           <Destination>Exchange</Destination>
           <Vias>
               <Via>School</Via>
           </Vias>
           <UseAllStopPoints>false</UseAllStopPoints>
           {0}
       </StandardService>
   </Services>
   """
    xml = service_template.format(patterns)

    pti = create_validator(None, None, OBSERVATION_ID)
    is_valid = pti.is_valid(TXCFile(xml))
    assert is_valid == expected
