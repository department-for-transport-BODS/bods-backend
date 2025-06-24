import time
from typing import Iterator

from common_layer.database.repos import (
    TransmodelServicePatternTracksRepo,
    TransmodelTrackRepo,
)
from pytest_mock import MockerFixture

from periodic_tasks.consolidate_tracks.app.handler_consolidate_tracks import (
    consolidate_tracks,
)


def test_consolidate_tracks_deletes_duplicates(mocker: MockerFixture):
    m_track_repo = mocker.create_autospec(TransmodelTrackRepo, instance=True)
    m_sp_track_repo = mocker.create_autospec(
        TransmodelServicePatternTracksRepo, instance=True
    )

    # Two stop point pairs containing duplicated tracks
    similar_tracks_data: list[tuple[tuple[str, str], list[tuple[int, int]]]] = [
        (("A", "B"), [(1, 2), (2, 3), (4, 5)]),
        (("C", "D"), [(6, 7)]),
        (("E", "F"), []),
    ]
    duplicate_tracks = [2, 3, 5, 7]
    similar_tracks_result: Iterator[tuple[tuple[str, str], list[tuple[int, int]]]] = (
        iter(similar_tracks_data)
    )
    m_track_repo.stream_similar_track_pairs_by_stop_points.return_value = (
        similar_tracks_result
    )

    start_time = int(time.perf_counter())
    stats = consolidate_tracks(
        track_repo=m_track_repo,
        sp_track_repo=m_sp_track_repo,
        threshold=20.0,
        start_time=start_time,
        dry_run=False,
    )

    # ServicePatternTracks referencing duplicated tracks should be updated
    expected_replace_calls = [(2, 1), (3, 1), (5, 4), (7, 6)]
    replace_calls = m_sp_track_repo.replace_service_pattern_track.call_args_list
    replace_calls = [
        (call_args.args[0], call_args.args[1]) for call_args in replace_calls
    ]
    assert sorted(replace_calls) == sorted(expected_replace_calls)

    # Duplicated tracks should be deleted
    delete_calls = m_track_repo.delete_by_id.call_args_list
    deleted_ids = [call_args.args[0] for call_args in delete_calls]

    assert sorted(deleted_ids) == sorted(duplicate_tracks)

    # Check stats
    assert stats["total_pairs_checked"] == 3
    assert stats["pairs_with_duplicates"] == 3
    assert stats["tracks_deleted"] == 4
    assert stats["vehicle_journey_fks_updated"] == 4
