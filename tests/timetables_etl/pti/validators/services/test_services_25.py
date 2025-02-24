"""
Test Services Observation 25
Mandatory elements incorrect in 'OutboundDescription' field.
"""

import pytest

from tests.timetables_etl.pti.validators.conftest import TXCFile, create_validator

from .conftest import DATA_DIR

OBSERVATION_ID = 25


@pytest.mark.parametrize(
    "xml, expected",
    [
        pytest.param(
            """
           <Lines>
               <Line id="L1">
                   <LineName>1</LineName>
                   <OutboundDescription>
                       <Origin>sdjfkjsdf</Origin>
                       <Destination>sdfjsjdfh</Destination>
                       <Description>A description</Description>
                   </OutboundDescription>
               </Line>
           </Lines>
           """,
            True,
            id="Valid Outbound Line Description",
        ),
        pytest.param(
            """
           <Lines>
               <Line id="L1">
                   <LineName>1</LineName>
                   <InboundDescription>
                       <Origin>sdjfkjsdf</Origin>
                       <Destination>sdfjsjdfh</Destination>
                       <Description>A description</Description>
                   </InboundDescription>
               </Line>
           </Lines>
           """,
            True,
            id="Valid Inbound Line Description",
        ),
        pytest.param(
            """
           <Services>
               <Service>
                   <Lines>
                       <Line id="L1">
                           <LineName>1</LineName>
                       </Line>
                   </Lines>
                   <StandardService>
                       <Origin>Putteridge High School</Origin>
                       <Destination>Church Street</Destination>
                   </StandardService>
               </Service>
           </Services>
           """,
            False,
            id="Invalid Missing Line Description",
        ),
    ],
)
def test_line_descriptions(xml: str, expected: bool):
    """
    Test validation of line descriptions
    Validates that lines have proper inbound or outbound descriptions
    """
    pti = create_validator(None, None, OBSERVATION_ID)
    is_valid = pti.is_valid(TXCFile(xml))
    assert is_valid if expected else not is_valid
