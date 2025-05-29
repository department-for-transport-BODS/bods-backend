import time
from typing import Iterator

from common_layer.database.repos import TransmodelTrackRepo
from pytest_mock import MockerFixture

from periodic_tasks.consolidate_tracks.app.handler_consolidate_tracks import (
    consolidate_tracks,
)


def test_consolidate_tracks_deletes_duplicates(mocker: MockerFixture):
    m_track_repo = mocker.create_autospec(TransmodelTrackRepo, instance=True)

    # Two stop point pairs containing duplicated tracks
    similar_tracks_data: list[tuple[tuple[str, str], list[tuple[int, int]]]] = [
        (("A", "B"), [(1, 2), (2, 3)]),
        (("C", "D"), [(4, 5)]),
        (("E", "F"), []),
    ]
    similar_tracks_result: Iterator[tuple[tuple[str, str], list[tuple[int, int]]]] = (
        iter(similar_tracks_data)
    )
    m_track_repo.stream_similar_track_pairs_json.return_value = similar_tracks_result

    start_time = int(time.perf_counter())
    stats = consolidate_tracks(
        track_repo=m_track_repo, threshold=20.0, start_time=start_time, dry_run=False
    )

    # Duplicated tracks should be deleted
    expected_deletions = [2, 3, 5]
    actual_calls = m_track_repo.delete_by_id.call_args_list
    deleted_ids = [call_args.args[0] for call_args in actual_calls]

    assert sorted(deleted_ids) == sorted(expected_deletions)

    # Check stats
    assert stats["total_pairs_checked"] == 3
    assert stats["pairs_with_duplicates"] == 2
    assert stats["tracks_deleted"] == 3
    assert stats["vehicle_journey_fks_updated"] == 3
