"""
Test Utils for working with Flexible Stops that require DB data
Unlike the ones in /txc which are independent
"""

import pytest

from tests.timetables_etl.factories.database.naptan import NaptanStopPointFactory
from timetables_etl.etl.app.transform.utils_stops_flexible import (
    map_stop_refs_to_naptan,
)


@pytest.mark.parametrize(
    "stop_refs,stop_data,expected_count",
    [
        pytest.param(
            ["stop1", "stop2"],
            [("stop1", "Stop 1"), ("stop2", "Stop 2")],
            2,
            id="Valid: All Stops Found",
        ),
        pytest.param(
            ["stop1", "missing_stop", "stop2"],
            [("stop1", "Stop 1"), ("stop2", "Stop 2")],
            2,
            id="Valid: Some Stops Missing",
        ),
        pytest.param(
            ["missing1", "missing2"],
            [("stop3", "Stop 3"), ("stop4", "Stop 4")],
            0,
            id="Valid: No Stops Found",
        ),
        pytest.param(
            [],
            [("stop1", "Stop 1"), ("stop2", "Stop 2")],
            0,
            id="Valid: Empty Stop Refs",
        ),
    ],
)
def test_map_stop_refs_to_naptan(
    stop_refs: list[str],
    stop_data: list[tuple[str, str]],
    expected_count: int,
) -> None:
    """
    Test mapping stop references to NaptanStopPoint objects
    """
    mapping = NaptanStopPointFactory.create_mapping(stop_data)
    result = map_stop_refs_to_naptan(stop_refs, mapping, "test_jp_id")
    assert len(result) == expected_count
