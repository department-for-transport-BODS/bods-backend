"""
Test Parsing the Top Level StopPoint
"""

import pytest
from lxml import etree

from periodic_tasks.naptan_cache.app.data_loader.parsers.parser_top_level import (
    parse_top_level,
)
from tests.periodic_tasks.naptan_cache.parsers.common import (
    create_stop_point,
    parse_xml_to_stop_point,
)


@pytest.mark.parametrize(
    ("xml_input", "expected_result", "expected_atco_found"),
    [
        pytest.param(
            create_stop_point(
                """
               <AtcoCode>0100BRP90310</AtcoCode>
               <NaptanCode>bstgwpa</NaptanCode>
               <LocalityName>Bristol</LocalityName>
               <StopType>BCT</StopType>
               <NptgLocalityRef>N0077020</NptgLocalityRef>
               <AdministrativeAreaRef>009</AdministrativeAreaRef>
           """
            ),
            {
                "AtcoCode": "0100BRP90310",
                "NaptanCode": "bstgwpa",
                "LocalityName": "Bristol",
                "StopType": "BCT",
                "NptgLocalityRef": "N0077020",
                "AdministrativeAreaRef": "009",
            },
            True,
            id="Complete TopLevel Data",
        ),
        pytest.param(
            create_stop_point(
                """
               <AtcoCode>0100BRP90310</AtcoCode>
               <NaptanCode>bstgwpa</NaptanCode>
           """
            ),
            {
                "AtcoCode": "0100BRP90310",
                "NaptanCode": "bstgwpa",
                "LocalityName": None,
                "StopType": None,
                "NptgLocalityRef": None,
                "AdministrativeAreaRef": None,
            },
            True,
            id="Partial TopLevel Data",
        ),
        pytest.param(
            create_stop_point(
                """
               <AtcoCode></AtcoCode>
               <NaptanCode></NaptanCode>
           """
            ),
            {
                "AtcoCode": None,
                "NaptanCode": None,
                "LocalityName": None,
                "StopType": None,
                "NptgLocalityRef": None,
                "AdministrativeAreaRef": None,
            },
            False,
            id="Empty Elements",
        ),
        pytest.param(
            create_stop_point(""),
            {
                "AtcoCode": None,
                "NaptanCode": None,
                "LocalityName": None,
                "StopType": None,
                "NptgLocalityRef": None,
                "AdministrativeAreaRef": None,
            },
            False,
            id="No TopLevel Data",
        ),
        pytest.param(
            create_stop_point(
                """
               <NaptanCode>bstgwpa</NaptanCode>
               <LocalityName>Bristol</LocalityName>
           """
            ),
            {
                "AtcoCode": None,
                "NaptanCode": "bstgwpa",
                "LocalityName": "Bristol",
                "StopType": None,
                "NptgLocalityRef": None,
                "AdministrativeAreaRef": None,
            },
            False,
            id="Missing AtcoCode",
        ),
    ],
)
def test_parse_top_level(
    xml_input: str,
    expected_result: dict[str, str | None],
    expected_atco_found: bool,
) -> None:
    """
    Test parse_top_level function with various input scenarios.
    """
    stop_point: etree._Element = parse_xml_to_stop_point(xml_input)
    result, atco_found = parse_top_level(stop_point)
    assert result == expected_result
    assert atco_found == expected_atco_found
