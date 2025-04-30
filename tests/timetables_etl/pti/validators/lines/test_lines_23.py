"""
Lines PTI Tests
"""

from unittest.mock import create_autospec

import pytest
from common_layer.dynamodb.client.naptan_stop_points import (
    NaptanStopPointDynamoDBClient,
)
from common_layer.xml.txc.models.txc_stoppoint.txc_stoppoint import TXCStopPoint

from tests.timetables_etl.pti.validators.conftest import TXCFile

from ..conftest import create_validator, run_validation
from .conftest import DATA_DIR

OBSERVATION_ID = 23


def test_validate_less_than_two_lines():
    """Test validation of service with single line"""
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
    xml = f"<Services>{service}</Services>"

    pti = create_validator(None, None, OBSERVATION_ID)
    is_valid = pti.is_valid(TXCFile(xml))
    assert is_valid


@pytest.mark.parametrize(
    "filename, expected",
    [
        pytest.param("nonrelatedlines.xml", False, id="Non Related Lines"),
        pytest.param(
            "relatedlinesbylocalityname.xml", True, id="Related Lines By Locality Name"
        ),
        pytest.param(
            "relatedlinesbyjp.xml", True, id="Related Lines By Journey Pattern"
        ),
        pytest.param("relatedlinesbystops.xml", True, id="Related Lines By Stops"),
    ],
)
def test_related_lines(filename: str, expected: bool) -> None:
    """Test validation of related lines in TXC files"""
    is_valid = run_validation(filename, DATA_DIR, OBSERVATION_ID)
    assert is_valid == expected


def test_non_related_with_stop_areas() -> None:
    """
    Test validation of non-related lines with matching stop areas
    The following atco codes come from nonrelatedlines.xml one stop in each line
    """
    l1stop = "9990000001"
    l1_n_stop = "9990000026"
    stop_areas_in_common = ["match"]

    m_stop_point_client = create_autospec(spec=NaptanStopPointDynamoDBClient)
    m_stop_point_client.get_by_atco_codes.return_value = (
        [
            TXCStopPoint.model_construct(
                AtcoCode=l1stop, StopAreas=stop_areas_in_common
            ),
            TXCStopPoint.model_construct(
                AtcoCode=l1_n_stop, StopAreas=stop_areas_in_common
            ),
        ],
        [],
    )

    is_valid = run_validation(
        "nonrelatedlines.xml", DATA_DIR, OBSERVATION_ID, m_stop_point_client
    )
    assert is_valid
