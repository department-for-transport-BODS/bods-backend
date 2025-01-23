"""
Pytest Fixtures
"""

from pathlib import Path
from unittest.mock import patch

import pytest

DATA_DIR = Path(__file__).parent.parent / "data/services"


@pytest.fixture
def m_stop_point_repo():
    """
    StopPointRepo Patch
    """
    with patch(
        "pti.app.validators.service.flexible_service.NaptanStopPointRepo"
    ) as m_repo:
        yield m_repo
