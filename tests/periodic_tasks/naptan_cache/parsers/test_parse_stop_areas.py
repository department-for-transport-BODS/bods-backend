"""
Test Parsing the StopAreas List
"""

import pytest
from lxml import etree

from periodic_tasks.naptan_cache.app.data_loader.parsers.parser_stop_areas import (
    parse_stop_areas,
)
from tests.periodic_tasks.naptan_cache.parsers.common import (
    create_stop_point,
    parse_xml_to_stop_point,
)


@pytest.mark.parametrize(
    ("xml_input", "expected"),
    [
        pytest.param(
            create_stop_point(
                """
               <StopAreas>
                   <StopAreaRef Status="active">010G0002</StopAreaRef>
               </StopAreas>
           """
            ),
            ["010G0002"],
            id="SingleActiveStopArea",
        ),
        pytest.param(
            create_stop_point(
                """
               <StopAreas>
                   <StopAreaRef Status="active">010G0002</StopAreaRef>
                   <StopAreaRef Status="active">010G0003</StopAreaRef>
                   <StopAreaRef Status="active">010G0004</StopAreaRef>
               </StopAreas>
           """
            ),
            ["010G0002", "010G0003", "010G0004"],
            id="MultipleActiveStopAreas",
        ),
        pytest.param(
            create_stop_point(
                """
               <StopAreas>
                   <StopAreaRef Status="active">010G0002</StopAreaRef>
                   <StopAreaRef Status="inactive">010G0003</StopAreaRef>
                   <StopAreaRef Status="active">010G0004</StopAreaRef>
               </StopAreas>
           """
            ),
            ["010G0002", "010G0004"],
            id="MixedStatusStopAreas",
        ),
        pytest.param(
            create_stop_point(
                """
               <StopAreas>
                   <StopAreaRef Status="inactive">010G0002</StopAreaRef>
               </StopAreas>
           """
            ),
            [],
            id="OnlyInactiveStopArea",
        ),
        pytest.param(
            create_stop_point(
                """
               <StopAreas>
                   <StopAreaRef Status="active"></StopAreaRef>
               </StopAreas>
           """
            ),
            [],
            id="EmptyStopAreaRef",
        ),
        pytest.param(
            create_stop_point("<StopAreas></StopAreas>"),
            [],
            id="EmptyStopAreas",
        ),
        pytest.param(
            create_stop_point(""),
            [],
            id="NoStopAreas",
        ),
    ],
)
def test_parse_stop_areas(xml_input: str, expected: list[str]) -> None:
    """
    Test parse_stop_areas function with various input scenarios.
    """
    stop_point: etree._Element = parse_xml_to_stop_point(xml_input)
    result: list[str] = parse_stop_areas(stop_point)
    assert result == expected
