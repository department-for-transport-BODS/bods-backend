"""
PTI Utils Tests
"""

from unittest.mock import MagicMock, patch

import pytest
from common_layer.database.repos.repo_otc import ServiceWithRegion
from pti.app.utils import get_service_in_scotland_from_db, is_service_in_scotland
from pti.app.utils.utils_scotland import SCOTLAND_TRAVELINE_REGIONS


def test_is_service_in_scotland() -> None:
    """
    Test if a service is in Scotland
    """
    cache = MagicMock()
    db = MagicMock()
    cache.get_or_compute.return_value = True

    result = is_service_in_scotland("PH0006633:01010001", cache, db)

    assert result is True

    _args, kwargs = cache.get_or_compute.call_args
    compute_fn = kwargs["compute_fn"]

    assert kwargs["key"] == "PH0006633-01010001-is-scottish-region"
    assert kwargs["ttl"] == 7200

    # Test that compute_fn calls the correct function
    with patch(
        "pti.app.utils.utils_scotland.get_service_in_scotland_from_db"
    ) as m_get_service_in_scotland_from_db:
        m_get_service_in_scotland_from_db.return_value = True
        result = compute_fn()
        m_get_service_in_scotland_from_db.assert_called_once_with(
            "PH0006633:01010001", db
        )


@patch("pti.app.utils.utils_scotland.OtcServiceRepo")
@pytest.mark.parametrize(
    ("traveline_region", "expected_result"),
    [
        pytest.param(
            SCOTLAND_TRAVELINE_REGIONS[0], True, id="Scottish Region Returns True"
        ),
        pytest.param(
            "NotScottishRegion", False, id="Non Scottish Region Returns False"
        ),
    ],
)
def test_get_service_in_scotland_from_db(
    m_service_repo: MagicMock, traveline_region: str, expected_result: bool
):
    """
    Test Getting Service in scotland from DB
    """
    m_service_repo.return_value.get_service_with_traveline_region.return_value = (
        ServiceWithRegion(service=MagicMock(), traveline_region=traveline_region)
    )
    service_ref = "PH0006633/01010001"

    result = get_service_in_scotland_from_db(service_ref, MagicMock())

    assert result is expected_result
    m_service_repo.return_value.get_service_with_traveline_region.assert_called_once_with(
        service_ref
    )
