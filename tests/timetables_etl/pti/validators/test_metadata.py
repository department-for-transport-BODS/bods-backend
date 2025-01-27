"""
Test Metadata Checks
"""

from unittest.mock import MagicMock

import pytest
from pti.app.validators.metadata import validate_modification_date_time


@pytest.mark.parametrize(
    ("root_attributes", "expected"),
    [
        pytest.param(
            {
                "RevisionNumber": "0",
                "ModificationDateTime": "2024-11-14T12:00:00",
                "CreationDateTime": "2024-11-14T12:00:00",
            },
            True,
            id="Initial Revision With Matching Timestamps",
        ),
        pytest.param(
            {
                "RevisionNumber": "0",
                "ModificationDateTime": "2024-11-14T12:00:00",
                "CreationDateTime": "2024-11-14T11:00:00",
            },
            False,
            id="Initial Revision With Different Timestamps",
        ),
        pytest.param(
            {
                "RevisionNumber": "1",
                "ModificationDateTime": "2024-11-14T12:00:00",
                "CreationDateTime": "2024-11-14T11:00:00",
            },
            True,
            id="Later Revision With Valid Timestamp Order",
        ),
        pytest.param(
            {
                "RevisionNumber": "1",
                "ModificationDateTime": "2024-11-14T12:00:00",
                "CreationDateTime": "2024-11-14T12:00:00",
            },
            False,
            id="Later Revision With Invalid Timestamp Order",
        ),
    ],
)
def test_validate_modification_date_time(root_attributes: dict, expected: bool):
    """
    Test Validating Modification datatime
    """
    mock_root = MagicMock()
    mock_root.attrib = root_attributes

    result = validate_modification_date_time(MagicMock(), [mock_root])
    assert result == expected
