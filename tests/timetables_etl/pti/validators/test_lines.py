from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from common_layer.pti.constants import PTI_SCHEMA_PATH
from common_layer.pti.models import Schema
from pti.validators.pti import PTIValidator

from tests.timetables_etl.pti.validators.conftest import JSONFile, TXCFile
from tests.timetables_etl.pti.validators.factories import SchemaFactory

DATA_DIR = Path(__file__).parent / "data" / "lines"


@pytest.fixture(autouse=True, scope="module")
def m_stop_point_repo():
    with patch("pti.validators.functions.NaptanStopPointRepo") as m_repo:
        yield m_repo


def test_validate_less_than_two_lines():
    service = """
    <Service>
        <ServiceCode>FIN50</ServiceCode>
        <Lines>
            <Line id="l_1">
                <LineName>A1</LineName>
            </Line>
        </Lines>
    </Service>
    """
    xml = "<Services>{0}</Services>".format(service)

    OBSERVATION_ID = 23
    schema = Schema.from_path(PTI_SCHEMA_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.model_dump_json())
    pti = PTIValidator(json_file, MagicMock(), MagicMock())
    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("nonrelatedlines.xml", False),
        ("relatedlinesbylocalityname.xml", True),
        ("relatedlinesbyjp.xml", True),
        ("relatedlinesbystops.xml", True),
    ],
)
def test_related_lines(filename, expected):
    OBSERVATION_ID = 23
    schema = Schema.from_path(PTI_SCHEMA_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.model_dump_json())
    pti = PTIValidator(json_file, MagicMock(), MagicMock())
    txc_path = DATA_DIR / filename
    with txc_path.open("r") as txc:
        is_valid = pti.is_valid(txc)
    assert is_valid == expected


def test_non_related_with_stop_areas(m_stop_point_repo):
    # The following atco codes come from nonrelatedlines.xml one stop in each line
    l1stop = "9990000001"
    l1Nstop = "9990000026"
    stop_areas_in_common = ["match"]
    m_stop_point_repo.return_value.get_stop_area_map.return_value = {
        l1stop: stop_areas_in_common,
        l1Nstop: stop_areas_in_common,
    }

    OBSERVATION_ID = 23
    schema = Schema.from_path(PTI_SCHEMA_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.model_dump_json())
    pti = PTIValidator(json_file, MagicMock(), MagicMock())
    txc_path = DATA_DIR / "nonrelatedlines.xml"
    with txc_path.open("r") as txc:
        assert pti.is_valid(txc)
