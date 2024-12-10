from unittest.mock import MagicMock, patch

import pytest
from common_layer.db.repositories.otc_service import ServiceWithRegion
from pti.constants import SCOTLAND_TRAVELINE_REGIONS
from pti.utils import get_service_in_scotland_from_db, is_service_in_scotland


@pytest.fixture(autouse=True, scope="module")
def m_db_manager():
    with patch("pti.utils.DbManager") as m_db_manager:
        yield m_db_manager


def test_is_service_in_scotland():
    cache = MagicMock()
    cache.get_or_compute.return_value = True

    result = is_service_in_scotland("PH0006633:01010001", cache)

    assert result is True

    args, kwargs = cache.get_or_compute.call_args
    compute_fn = kwargs["compute_fn"]

    assert kwargs["key"] == "PH0006633-01010001-is-scottish-region"
    assert kwargs["ttl"] == 7200

    # Test that compute_fn calls the correct function
    with patch(
        "pti.utils.get_service_in_scotland_from_db"
    ) as m_get_service_in_scotland_from_db:
        m_get_service_in_scotland_from_db.return_value = True
        result = compute_fn()
        m_get_service_in_scotland_from_db.assert_called_once_with("PH0006633:01010001")


@patch("pti.utils.OtcServiceRepository")
@pytest.mark.parametrize(
    "traveline_region, expected_result",
    [(SCOTLAND_TRAVELINE_REGIONS[0], True), ("NotScottishRegion", False)],
)
def test_get_service_in_scotland_from_db(
    m_service_repo, traveline_region, expected_result
):
    m_service_repo.return_value.get_service_with_traveline_region.return_value = (
        ServiceWithRegion(service=MagicMock(), traveline_region=traveline_region)
    )
    service_ref = "PH0006633/01010001"

    result = get_service_in_scotland_from_db(service_ref)

    assert result is expected_result
    m_service_repo.return_value.get_service_with_traveline_region.assert_called_once_with(
        service_ref
    )
