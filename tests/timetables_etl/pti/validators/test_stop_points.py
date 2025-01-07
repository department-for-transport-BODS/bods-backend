from pathlib import Path
from unittest.mock import MagicMock

import pytest
from common_layer.pti.constants import PTI_SCHEMA_PATH
from common_layer.pti.models import Schema
from lxml import etree
from pti.validators.functions import validate_non_naptan_stop_points
from pti.validators.pti import PTIValidator

from tests.timetables_etl.pti.validators.conftest import JSONFile
from tests.timetables_etl.pti.validators.factories import SchemaFactory

DATA_DIR = Path(__file__).parent / "data" / "stop_points"


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("bodp3615stoppoints.xml", True),
        ("bodp3615stoppointsfail2month.xml", False),
        ("bodp3615stoppointsfailnodate.xml", False),
        ("stoppointsinheritfromservice2months.xml", True),
        ("stoppointsinheritfromservice2monthsplus.xml", False),
        ("stoppointsinheritstartdatefromservice.xml", True),
        ("stoppointsinheritenddatefromservice.xml", True),
    ],
)
def test_non_naptan_stop_points(filename, expected):
    OBSERVATION_ID = 28
    schema = Schema.from_path(PTI_SCHEMA_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]

    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.model_dump_json())
    pti = PTIValidator(json_file, MagicMock(), MagicMock())

    txc_path = DATA_DIR / filename
    with txc_path.open("r") as txc:
        is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("stop_point_missing_mode.xml", False),
        ("stop_point_w_bus_mode.xml", False),
        ("stop_point_w_coach_mode.xml", True),
        ("stop_point_w_bus_mode_success.xml", True),
        ("stop_point_w_bus_mode_blank_enddate.xml", True),
        ("stop_point_w_bus_mode_wo_operating_profile.xml", True),
    ],
)
def test_check_stop_point_two_months(filename, expected):
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    string_xml = DATA_DIR / filename
    with string_xml.open("r") as txc_xml:
        doc = etree.parse(txc_xml)
        elements = doc.xpath("//x:StopPoint", namespaces=NAMESPACE)
        actual = validate_non_naptan_stop_points("", elements)
        assert actual == expected
