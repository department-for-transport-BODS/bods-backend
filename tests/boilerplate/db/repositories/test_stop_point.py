from unittest.mock import MagicMock

import pytest
from db.repositories.stop_point import StopPointRepository
from exceptions.pipeline_exceptions import PipelineException

from tests.mock_db import MockedDB, naptan_stoppoint


def test_get_count():
    mock_db = MockedDB()

    # Filters
    atco_codes = ["atco1", "atco2"]
    bus_stop_type = "FLX"
    stop_type = "BCT"

    # StopPoints matching filters
    match_1 = naptan_stoppoint(atco_code=atco_codes[0], bus_stop_type=bus_stop_type, stop_type=stop_type)
    match_2 = naptan_stoppoint(atco_code=atco_codes[1], bus_stop_type=bus_stop_type, stop_type=stop_type)

    # StopPoints not matching filters
    not_match_1 = naptan_stoppoint(atco_code="mismatching-atco-code", bus_stop_type=bus_stop_type, stop_type=stop_type)
    not_match_2 = naptan_stoppoint(
        atco_code=atco_codes[0], bus_stop_type=bus_stop_type, stop_type="mismatching-stop-type"
    )

    with mock_db.session as session:
        session.bulk_save_objects([match_1, match_2, not_match_1, not_match_2])
        session.commit()

    repo = StopPointRepository(mock_db)
    result = repo.get_count(atco_codes=atco_codes, bus_stop_type=bus_stop_type, stop_type=stop_type)

    assert result == 2


def test_get_count_non_found():
    mock_db = MockedDB()

    # Filters
    atco_codes = ["atco1", "atco2"]

    # StopPoint not matching filters
    not_match_1 = naptan_stoppoint(atco_code="mismatching-atco-code")

    with mock_db.session as session:
        session.add(not_match_1)
        session.commit()

    repo = StopPointRepository(mock_db)
    result = repo.get_count(atco_codes=atco_codes)

    assert result == 0


def test_get_count_exception():
    mock_db = MockedDB()

    m_session = MagicMock()
    m_session.__enter__.return_value.query = MagicMock(side_effect=Exception("DB Exception"))
    mock_db.session = m_session

    repo = StopPointRepository(mock_db)

    with pytest.raises(PipelineException):
        repo.get_count(atco_codes=[])


def test_get_stop_area_map():
    db = MockedDB()
    stops = [
        naptan_stoppoint(atco_code="270002700155", stop_areas=["Area1"]),
        naptan_stoppoint(atco_code="270002700156", stop_areas=["Area2"]),
        naptan_stoppoint(atco_code="270002700156", stop_areas=[]),
    ]
    expected_result = {"270002700155": ["Area1"], "270002700156": ["Area2"]}
    with db.session as session:
        session.bulk_save_objects(stops)
        session.commit()

    repository = StopPointRepository(db)
    result = repository.get_stop_area_map()

    assert result == expected_result


def test_get_stop_area_map_no_result():
    db = MockedDB()
    stops = [
        naptan_stoppoint(atco_code="270002700156", stop_areas=[]),
    ]
    expected_result = {}

    with db.session as session:
        session.bulk_save_objects(stops)
        session.commit()

    repository = StopPointRepository(db)
    result = repository.get_stop_area_map()

    assert result == expected_result


def test_get_stop_area_map_exception():
    mock_db = MockedDB()

    m_session = MagicMock()
    m_session.__enter__.return_value.query = MagicMock(side_effect=Exception("DB Exception"))
    mock_db.session = m_session

    repo = StopPointRepository(mock_db)

    with pytest.raises(PipelineException, match="Error retrieving stops excluding empty stop areas."):
        repo.get_stop_area_map()
