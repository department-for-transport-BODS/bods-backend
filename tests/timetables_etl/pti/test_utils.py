from unittest.mock import MagicMock, patch
import pytest
from db.repositories.otc_service import ServiceWithRegion
from pti.constants import SCOTLAND_TRAVELINE_REGIONS
from pti.utils import is_service_in_scotland


@pytest.fixture(autouse=True, scope="module")
def m_db_manager():
    with patch("pti.utils.DbManager") as m_db_manager:
        yield m_db_manager


@patch("pti.utils.OtcServiceRepository")
@pytest.mark.parametrize(
    "traveline_region, expected_result", [(SCOTLAND_TRAVELINE_REGIONS[0], True), ("NotScottishRegion", False)]
)
def test_is_service_in_scotland_false(m_service_repo, traveline_region, expected_result):
    m_service_repo.return_value.get_service_with_traveline_region.return_value = ServiceWithRegion(
        service=MagicMock(), traveline_region=traveline_region
    )
    service_ref = "PH0006633/01010001"

    result = is_service_in_scotland(service_ref)

    assert result is expected_result
    m_service_repo.return_value.get_service_with_traveline_region.assert_called_once_with(service_ref)
