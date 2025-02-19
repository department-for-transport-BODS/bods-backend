"""
Test Utils for working with Flexible Stops that require DB data
Unlike the ones in /txc which are independent
"""

import pytest

from tests.factories.database.naptan import NaptanStopPointFactory
from timetables_etl.etl.app.helpers.dataclasses.stop_points import NonExistentNaptanStop
from timetables_etl.etl.app.transform.utils_stops_flexible import (
    map_stop_refs_to_naptan,
)


@pytest.mark.parametrize(
    "stop_refs,naptan_stop_data,non_existent_stop_data,expected_count",
    [
        pytest.param(
            ["stop1", "stop2"],
            [("stop1", "Stop 1"), ("stop2", "Stop 2")],
            [],
            2,
            id="Valid: All Stops Found",
        ),
        pytest.param(
            ["stop1", "non_existent_stop_1", "stop2"],
            [("stop1", "Stop 1"), ("stop2", "Stop 2")],
            [("non_existent_stop_1", "NonExistentStop 1")],
            2,
            id="Valid: Some Stops Missing",
        ),
        pytest.param(
            ["non_existent_stop_1", "non_existent_stop_2"],
            [("stop3", "Stop 3"), ("stop4", "Stop 4")],
            [
                ("non_existent_stop_1", "NonExistentStop 1"),
                ("non_existent_stop_2", "NonExistentStop 2"),
            ],
            0,
            id="Valid: No Stops Found",
        ),
        pytest.param(
            [],
            [("stop1", "Stop 1"), ("stop2", "Stop 2")],
            [],
            0,
            id="Valid: Empty Stop Refs",
        ),
    ],
)
def test_map_stop_refs_to_naptan(
    stop_refs: list[str],
    naptan_stop_data: list[tuple[str, str]],
    non_existent_stop_data: list[tuple[str, str]],
    expected_count: int,
) -> None:
    """
    Test mapping stop references to NaptanStopPoint objects
    """
    mapping = NaptanStopPointFactory.create_mapping(naptan_stop_data)
    non_existent_stops = {
        atco: NonExistentNaptanStop(atco_code=atco, common_name=name)
        for atco, name in non_existent_stop_data
    }
    mapping.update(non_existent_stops)
    result = map_stop_refs_to_naptan(stop_refs, mapping, "test_jp_id")
    assert len(result) == expected_count


def test_map_stop_refs_to_naptan_stop_not_found():
    """
    Test the case that a stop ref isn't found in the stop point mapping
    """
    stop_refs = ["NotFoundAtcoCode"]
    mapping = NaptanStopPointFactory.create_mapping([("stop_1", "Stop1")])
    with pytest.raises(
        ValueError,
        match="Stop referenced in FlexibleJourneyPattern not found in stop map",
    ):
        map_stop_refs_to_naptan(stop_refs, mapping, "test_jp_id")
