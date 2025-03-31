import pytest
from common_layer.database.models import TransmodelServicePatternStop
from common_layer.xml.txc.models import TXCJourneyPatternTimingLink

from tests.factories.database.transmodel import TransmodelServicePatternStopFactory
from tests.timetables_etl.factories.txc import (
    TXCJourneyPatternStopUsageFactory,
    TXCJourneyPatternTimingLinkFactory,
)
from timetables_etl.etl.app.transform.service_pattern_stops import is_duplicate_stop


@pytest.mark.parametrize(
    "current_stop_ref, current_sequence, previous_stop, previous_link, expected",
    [
        pytest.param(
            "15800722",
            0,
            None,
            None,
            False,
            id="No previous stop",
        ),
        pytest.param(
            "15800722",
            2,
            TransmodelServicePatternStopFactory(
                sequence_number=1, atco_code="15800722"
            ),
            TXCJourneyPatternTimingLinkFactory(
                From=TXCJourneyPatternStopUsageFactory(StopPointRef="15800722"),
                To=TXCJourneyPatternStopUsageFactory(StopPointRef="15800722"),
            ),
            False,
            id="Previous link has the same From/To",
        ),
        pytest.param(
            "15800722",
            2,
            TransmodelServicePatternStopFactory(
                sequence_number=1, atco_code="15800722"
            ),
            TXCJourneyPatternTimingLinkFactory(
                From=TXCJourneyPatternStopUsageFactory(StopPointRef="15800721"),
                To=TXCJourneyPatternStopUsageFactory(StopPointRef="15800722"),
            ),
            True,
            id="Is duplicate stop",
        ),
        pytest.param(
            "15800723",
            2,
            TransmodelServicePatternStopFactory(
                sequence_number=1, atco_code="15800722"
            ),
            TXCJourneyPatternTimingLinkFactory(
                From=TXCJourneyPatternStopUsageFactory(StopPointRef="15800722"),
                To=TXCJourneyPatternStopUsageFactory(StopPointRef="15800723"),
            ),
            False,
            id="Is not duplicate (previous_stop.atco_code != current_stop_ref)",
        ),
    ],
)
def test_is_duplicate_stop(
    current_stop_ref: str,
    current_sequence: int,
    previous_stop: TransmodelServicePatternStop | None,
    previous_link: TXCJourneyPatternTimingLink | None,
    expected: bool,
):
    result = is_duplicate_stop(
        current_stop_ref=current_stop_ref,
        current_sequence=current_sequence,
        previous_stop=previous_stop,
        previous_link=previous_link,
    )
    assert result == expected
