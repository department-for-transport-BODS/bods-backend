"""
Test Service Helpers
"""

import pytest

from timetables_etl.etl.app.txc.helpers.service import (
    extract_flexible_pattern_stop_refs,
)
from timetables_etl.etl.app.txc.models.txc_service_flexible import (
    TXCFixedStopUsage,
    TXCFlexibleJourneyPattern,
    TXCFlexibleStopUsage,
)


@pytest.mark.parametrize(
    "flexible_jp,expected_refs",
    [
        pytest.param(
            TXCFlexibleJourneyPattern(
                id="jp_1",
                Direction="outbound",
                StopPointsInSequence=[
                    TXCFixedStopUsage(
                        StopPointRef="02903501", TimingStatus="otherPoint"
                    ),
                    TXCFlexibleStopUsage(StopPointRef="02901353"),
                ],
                FlexibleZones=[],
            ),
            ["02903501", "02901353"],
            id="Valid: StopPointsInSequence Only",
        ),
        pytest.param(
            TXCFlexibleJourneyPattern(
                id="jp_1",
                Direction="outbound",
                StopPointsInSequence=[],
                FlexibleZones=[
                    TXCFlexibleStopUsage(StopPointRef="02901354"),
                ],
            ),
            ["02901354"],
            id="Valid: FlexibleZones Only",
        ),
        pytest.param(
            TXCFlexibleJourneyPattern(
                id="jp_1",
                Direction="outbound",
                StopPointsInSequence=[
                    TXCFixedStopUsage(
                        StopPointRef="02903501", TimingStatus="otherPoint"
                    ),
                ],
                FlexibleZones=[
                    TXCFlexibleStopUsage(StopPointRef="02901354"),
                ],
            ),
            ["02903501", "02901354"],
            id="Valid: Both StopPointsInSequence and FlexibleZones",
        ),
        pytest.param(
            TXCFlexibleJourneyPattern(
                id="jp_1",
                Direction="outbound",
                StopPointsInSequence=[],
                FlexibleZones=[],
            ),
            [],
            id="Valid: Empty Pattern",
        ),
    ],
)
def test_extract_flexible_pattern_stop_refs(
    flexible_jp: TXCFlexibleJourneyPattern,
    expected_refs: list[str],
) -> None:
    """
    Test extracting stop references from a flexible journey pattern
    """
    result = extract_flexible_pattern_stop_refs(flexible_jp)
    assert result == expected_refs
