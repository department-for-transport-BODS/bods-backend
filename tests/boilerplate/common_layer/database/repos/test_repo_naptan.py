from unittest.mock import MagicMock, patch

import pytest
from common_layer.database.repos.repo_naptan import NaptanStopPointRepo
from common_layer.exceptions.pipeline_exceptions import PipelineException

from tests.factories.database.naptan import NaptanStopPointFactory


def test_get_count(test_db):

    # Filters
    atco_codes = ["atco1", "atco2"]
    bus_stop_type = "FLX"
    stop_type = "BCT"

    # StopPoints matching filters
    match_1 = NaptanStopPointFactory.create(
        atco_code=atco_codes[0], bus_stop_type=bus_stop_type, stop_type=stop_type
    )
    match_2 = NaptanStopPointFactory.create(
        atco_code=atco_codes[1], bus_stop_type=bus_stop_type, stop_type=stop_type
    )

    # StopPoints not matching filters
    not_match_1 = NaptanStopPointFactory.create(
        atco_code="mismatching-atco-code",
        bus_stop_type=bus_stop_type,
        stop_type=stop_type,
    )

    with test_db.session_scope() as session:
        session.bulk_save_objects([match_1, match_2, not_match_1])
        session.commit()

    repo = NaptanStopPointRepo(test_db)
    result = repo.get_count(
        atco_codes=atco_codes, bus_stop_type=bus_stop_type, stop_type=stop_type
    )

    assert result == 2


def test_get_count_non_found(test_db):

    # Filters
    atco_codes = ["atco1", "atco2"]

    # StopPoint not matching filters
    not_match_1 = NaptanStopPointFactory.create(atco_code="mismatching-atco-code")

    with test_db.session_scope() as session:
        session.add(not_match_1)
        session.commit()

    repo = NaptanStopPointRepo(test_db)
    result = repo.get_count(atco_codes=atco_codes)

    assert result == 0


def test_get_count_exception(test_db):
    m_session = MagicMock()
    m_session.return_value.__enter__.return_value.query = MagicMock(
        side_effect=Exception("DB Exception")
    )

    with patch.object(test_db, "session_scope", m_session):
        repo = StopPointRepo(test_db)

        with pytest.raises(PipelineException):
            repo.get_count(atco_codes=[])


def test_get_stop_area_map(test_db):
    stops = [
        NaptanStopPointFactory.create(atco_code="270002700155", stop_areas=["Area1"]),
        NaptanStopPointFactory.create(atco_code="270002700156", stop_areas=["Area2"]),
        NaptanStopPointFactory.create(atco_code="270002700157", stop_areas=[]),
    ]
    expected_result = {"270002700155": ["Area1"], "270002700156": ["Area2"]}
    with test_db.session_scope() as session:
        session.bulk_save_objects(stops)
        session.commit()

    repository = NaptanStopPointRepo(test_db)
    result = repository.get_stop_area_map()

    assert result == expected_result


def test_get_stop_area_map_no_result(test_db):
    stops = [
        NaptanStopPointFactory.create(atco_code="270002700156", stop_areas=[]),
    ]
    expected_result = {}

    with test_db.session_scope() as session:
        session.bulk_save_objects(stops)
        session.commit()

    repository = NaptanStopPointRepo(test_db)
    result = repository.get_stop_area_map()

    assert result == expected_result


def test_get_stop_area_map_exception(test_db):
    m_session = MagicMock()
    m_session.return_value.__enter__.return_value.query = MagicMock(
        side_effect=Exception("DB Exception")
    )
    with patch.object(test_db, "session_scope", m_session):
        repo = NaptanStopPointRepo(test_db)

        with pytest.raises(
            PipelineException,
            match="Error retrieving stops excluding empty stop areas.",
        ):
            repo.get_stop_area_map()
