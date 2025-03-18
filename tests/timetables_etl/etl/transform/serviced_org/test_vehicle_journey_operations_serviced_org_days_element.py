"""
Test the Days Element
"""

import pytest
from common_layer.database.models import (
    TransmodelServicedOrganisations,
    TransmodelServicedOrganisationVehicleJourney,
)
from common_layer.xml.txc.models import (
    TXCServicedOrganisation,
    TXCServicedOrganisationDatePattern,
    TXCServicedOrganisationDays,
)

from tests.factories.database.transmodel import TransmodelVehicleJourneyFactory
from timetables_etl.etl.app.transform.vehicle_journey_operations_serviced_org import (
    process_days_element,
)


def process_days_element_test_helper(
    working_days_refs: list[str],
    holiday_refs: list[str],
    is_operation_day: bool,
    expected_counts: tuple[int, int],
    mock_serviced_orgs: dict[str, TransmodelServicedOrganisations],
    mock_txc_serviced_orgs: dict[str, TXCServicedOrganisation],
) -> None:
    """Helper function for testing process_days_element with common logic"""
    # Given
    days = TXCServicedOrganisationDays(
        WorkingDays=working_days_refs,
        Holidays=holiday_refs,
    )

    # Only include refs that exist in the mocks
    filtered_working_days = [
        ref for ref in working_days_refs if ref in mock_serviced_orgs
    ]
    filtered_holidays = [ref for ref in holiday_refs if ref in mock_serviced_orgs]

    # Adjust expected counts based on filtered refs and operation type
    expected_vj_count = len(filtered_working_days) + len(filtered_holidays)

    expected_pattern_count = len(filtered_working_days) + len(filtered_holidays)

    if expected_counts != (expected_vj_count, expected_pattern_count):
        expected_counts = (expected_vj_count, expected_pattern_count)

    # When - process element
    vj_records, working_patterns = process_days_element(
        days=days,
        is_operation_day=is_operation_day,
        vehicle_journey=TransmodelVehicleJourneyFactory.create_with_id(100),
        serviced_orgs=mock_serviced_orgs,
        txc_serviced_orgs=mock_txc_serviced_orgs,
    )

    # Then
    assert len(vj_records) == expected_counts[0]
    assert len(working_patterns) == expected_counts[1]

    # Verify correct object types
    for vj in vj_records:
        assert isinstance(vj, TransmodelServicedOrganisationVehicleJourney)

    for _, patterns in working_patterns:
        assert isinstance(patterns, list)
        assert all(isinstance(p, TXCServicedOrganisationDatePattern) for p in patterns)


@pytest.mark.parametrize(
    "working_days_refs, holiday_refs, expected_counts",
    [
        pytest.param(
            ["SCH"],
            ["Holiday1"],
            (2, 2),
            id="One working day and one holiday",
        ),
        pytest.param(
            ["SCH", "MVSERVLESS"],
            [],
            (2, 2),
            id="Two working days, no holidays",
        ),
        pytest.param(
            [],
            ["Holiday1"],
            (1, 1),
            id="No working days, one holiday",
        ),
        pytest.param(
            [],
            [],
            (0, 0),
            id="Empty lists",
        ),
    ],
)
def test_process_days_element_operation(
    working_days_refs: list[str],
    holiday_refs: list[str],
    expected_counts: tuple[int, int],
    mock_serviced_orgs: dict[str, TransmodelServicedOrganisations],
    mock_txc_serviced_orgs: dict[str, TXCServicedOrganisation],
) -> None:
    """Test processing a TXCServicedOrganisationDays element for DaysOfOperation"""
    process_days_element_test_helper(
        working_days_refs=working_days_refs,
        holiday_refs=holiday_refs,
        is_operation_day=True,
        expected_counts=expected_counts,
        mock_serviced_orgs=mock_serviced_orgs,
        mock_txc_serviced_orgs=mock_txc_serviced_orgs,
    )


@pytest.mark.parametrize(
    "working_days_refs, holiday_refs, expected_counts",
    [
        pytest.param(
            ["MVSERVLESS"],
            [],
            (1, 1),
            id="One working day, no holidays",
        ),
        pytest.param(
            [],
            ["Holiday1"],
            (1, 1),
            id="No working days, one holiday",
        ),
        pytest.param(
            ["MVSERVLESS"],
            ["Holiday1"],
            (2, 2),
            id="Both working day and holiday",
        ),
        pytest.param(
            [],
            [],
            (0, 0),
            id="Empty lists",
        ),
    ],
)
def test_process_days_element_non_operation(
    working_days_refs: list[str],
    holiday_refs: list[str],
    expected_counts: tuple[int, int],
    mock_serviced_orgs: dict[str, TransmodelServicedOrganisations],
    mock_txc_serviced_orgs: dict[str, TXCServicedOrganisation],
) -> None:
    """Test processing a TXCServicedOrganisationDays element for DaysOfNonOperation"""
    process_days_element_test_helper(
        working_days_refs=working_days_refs,
        holiday_refs=holiday_refs,
        is_operation_day=False,
        expected_counts=expected_counts,
        mock_serviced_orgs=mock_serviced_orgs,
        mock_txc_serviced_orgs=mock_txc_serviced_orgs,
    )
