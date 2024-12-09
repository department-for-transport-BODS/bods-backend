from unittest.mock import MagicMock, patch

import pytest
from common_layer.db.repositories.otc_service import ServiceWithRegion
from pti.constants import SCOTLAND_TRAVELINE_REGIONS
from pti.utils import is_service_in_scotland


@pytest.fixture(autouse=True, scope="module")
def m_db_manager():
    with patch("pti.utils.DbManager") as m_db_manager:
        yield m_db_manager


@patch("pti.utils.DynamoDB")
@patch("pti.utils.OtcServiceRepository")
@pytest.mark.parametrize(
    "traveline_region, expected_result",
    [(SCOTLAND_TRAVELINE_REGIONS[0], True), ("NotScottishRegion", False)],
)
def test_is_service_in_scotland_not_cached(
    m_service_repo, m_dynamodb, traveline_region, expected_result
):
    m_dynamodb.get.return_value = None
    m_service_repo.return_value.get_service_with_traveline_region.return_value = (
        ServiceWithRegion(service=MagicMock(), traveline_region=traveline_region)
    )
    service_ref = "PH0006633/01010001"

    result = is_service_in_scotland(service_ref)

    assert result is expected_result
    m_service_repo.return_value.get_service_with_traveline_region.assert_called_once_with(
        service_ref
    )
    m_dynamodb.put.assert_called_once_with(
        "PH0006633/01010001-is-scottish-region", expected_result, ttl=7200
    )


@patch("pti.utils.DynamoDB")
@patch("pti.utils.OtcServiceRepository")
@pytest.mark.parametrize(
    "traveline_region, expected_result",
    [(SCOTLAND_TRAVELINE_REGIONS[0], True), ("NotScottishRegion", False)],
)
def test_is_service_in_scotland_cache(
    m_service_repo, m_dynamodb, traveline_region, expected_result
):
    m_dynamodb.get.return_value = expected_result
    m_service_repo.return_value.get_service_with_traveline_region.return_value = (
        ServiceWithRegion(service=MagicMock(), traveline_region=traveline_region)
    )
    service_ref = "PH0006633/01010001"

    result = is_service_in_scotland(service_ref)

    assert result is expected_result
    m_dynamodb.get.assert_called_once_with("PH0006633/01010001-is-scottish-region")
    m_service_repo.return_value.get_service_with_traveline_region.assert_not_called(), "should return cached value without calling repo"
    m_dynamodb.put.assert_not_called()
