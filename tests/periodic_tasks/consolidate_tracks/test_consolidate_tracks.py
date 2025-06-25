import time

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

    # Simulate similar track pairs grouped by stop point pair
    similar_tracks_data: list[tuple[tuple[str, str], list[tuple[int, int]]]] = [
        (("A", "B"), [(1, 2), (2, 3), (4, 5)]),  # Grouped: [1,2,3], [4,5]
        (("C", "D"), [(6, 7)]),  # Grouped: [6,7]
        (("E", "F"), []),  # No duplicates
    ]
    similar_tracks_result = iter(similar_tracks_data)
    m_track_repo.stream_similar_track_pairs_by_stop_points.return_value = (
        similar_tracks_result
    )

    # mock responses used for stats
    m_track_repo.bulk_delete_by_ids.return_value = 1
    m_sp_track_repo.bulk_replace_service_pattern_tracks.return_value = 1

    start_time = int(time.perf_counter())
    stats = consolidate_tracks(
        track_repo=m_track_repo,
        sp_track_repo=m_sp_track_repo,
        threshold=20.0,
        start_time=start_time,
        dry_run=False,
    )

    # Expected groups -> canonical ID : [duplicate IDs]
    expected_bulk_replace_calls = [
        ([2, 3], 1),
        ([5], 4),
        ([7], 6),
    ]

    # Check bulk_replace_service_pattern_tracks calls
    replace_calls = m_sp_track_repo.bulk_replace_service_pattern_tracks.call_args_list
    parsed_replace_calls = [(args.args[0], args.args[1]) for args in replace_calls]
    assert sorted(parsed_replace_calls) == sorted(expected_bulk_replace_calls)

    # Check bulk deletes
    expected_deleted_ids = [2, 3, 5, 7]
    delete_calls = m_track_repo.bulk_delete_by_ids.call_args_list
    deleted_id_lists = [args.args[0] for args in delete_calls]
    flattened_ids = [track_id for sublist in deleted_id_lists for track_id in sublist]
    assert sorted(flattened_ids) == sorted(expected_deleted_ids)

    # Stats assertions
    assert stats["total_pairs_checked"] == 3
    assert stats["pairs_with_duplicates"] == 3
    assert stats["tracks_to_delete"] == 4
    assert stats["tracks_deleted"] == 3
    assert stats["fks_updated"] == 3
