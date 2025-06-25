from common_layer.database import SqlDB
from common_layer.database.repos import TransmodelServicePatternTracksRepo

from tests.factories.database.junction import TransmodelServicePatternTracksFactory


def test_bulk_replace_service_pattern_tracks(test_db: SqlDB):
    track_id_to_replace_1 = 2
    track_id_to_replace_2 = 3
    replacement_id = 4

    spt_1 = TransmodelServicePatternTracksFactory.create(
        tracks_id=track_id_to_replace_1, service_pattern_id=5
    )
    spt_2 = TransmodelServicePatternTracksFactory.create(
        tracks_id=track_id_to_replace_1, service_pattern_id=6
    )
    spt_3 = TransmodelServicePatternTracksFactory.create(
        tracks_id=track_id_to_replace_2, service_pattern_id=7
    )
    spt_4 = TransmodelServicePatternTracksFactory.create(
        tracks_id=99, service_pattern_id=8  # should not be updated
    )

    with test_db.session_scope() as session:
        session.add_all([spt_1, spt_2, spt_3, spt_4])
        session.flush()
        spt_1_id, spt_2_id, spt_3_id, spt_4_id = spt_1.id, spt_2.id, spt_3.id, spt_4.id
        session.commit()

    repo = TransmodelServicePatternTracksRepo(test_db)
    repo.bulk_replace_service_pattern_tracks(
        old_ids=[track_id_to_replace_1, track_id_to_replace_2],
        new_id=replacement_id,
    )

    spt1_updated = repo.get_by_id(spt_1_id)
    spt2_updated = repo.get_by_id(spt_2_id)
    spt3_updated = repo.get_by_id(spt_3_id)
    spt4 = repo.get_by_id(spt_4_id)

    assert spt1_updated.tracks_id == replacement_id
    assert spt2_updated.tracks_id == replacement_id
    assert spt3_updated.tracks_id == replacement_id
    assert spt4.tracks_id == 99, "track id should not change"
