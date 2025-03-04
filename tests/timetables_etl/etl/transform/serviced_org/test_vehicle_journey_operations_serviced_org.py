"""
Test Service Org parsing
"""

from datetime import date

import pytest
from common_layer.database.models import (
    TransmodelServicedOrganisations,
    TransmodelServicedOrganisationVehicleJourney,
)
from common_layer.xml.txc.models import (
    TXCServicedOrganisation,
    TXCServicedOrganisationDatePattern,
    TXCServicedOrganisationDays,
    TXCServicedOrganisationDayType,
)
from etl.app.transform.vehicle_journey_operations_serviced_org import (
    create_serviced_org_vehicle_journey,
    create_serviced_organisation_vehicle_journeys,
    process_org_ref,
)

from tests.factories.database.transmodel import TransmodelVehicleJourneyFactory


@pytest.mark.parametrize(
    "org_ref, operating_on_working_days, expected_id, expected_op_flag",
    [
        pytest.param(
            "SCH", True, 1, True, id="School org with working days flag set to True"
        ),
        pytest.param(
            "MVSERVLESS",
            False,
            2,
            False,
            id="MVSERVLESS org with working days flag set to False",
        ),
        pytest.param(
            "Holiday1",
            True,
            3,
            True,
            id="Holiday org with working days flag set to True",
        ),
    ],
)
def test_create_serviced_org_vehicle_journey(
    org_ref,
    operating_on_working_days,
    expected_id,
    expected_op_flag,
    mock_serviced_orgs,
):
    """Test that a serviced organisation vehicle journey record is created correctly"""
    result = create_serviced_org_vehicle_journey(
        org_ref=org_ref,
        operating_on_working_days=operating_on_working_days,
        vehicle_journey=TransmodelVehicleJourneyFactory.create_with_id(100),
        serviced_orgs=mock_serviced_orgs,
    )

    assert isinstance(result, TransmodelServicedOrganisationVehicleJourney)
    assert result.operating_on_working_days == expected_op_flag
    assert result.serviced_organisation_id == expected_id
    assert result.vehicle_journey_id == 100


@pytest.mark.parametrize(
    "org_ref, operating_on_working_days, exists_in_tm, exists_in_txc, expected_result",
    [
        pytest.param(
            "SCH", True, True, True, (True, True), id="Org exists in both lookups"
        ),
        pytest.param(
            "MISSING",
            True,
            False,
            False,
            (None, []),
            id="Org missing from both lookups",
        ),
        pytest.param(
            "TM_ONLY", True, True, False, (None, []), id="Org exists only in TM lookup"
        ),
        pytest.param(
            "TXC_ONLY",
            True,
            False,
            True,
            (None, []),
            id="Org exists only in TXC lookup",
        ),
    ],
)
def test_process_org_ref(
    org_ref,
    operating_on_working_days,
    exists_in_tm,
    exists_in_txc,
    expected_result,
    mock_serviced_orgs,
    mock_txc_serviced_orgs,
):
    """Test processing a single organisation reference"""
    # Prepare test data based on parameters
    serviced_orgs = {}
    txc_serviced_orgs = {}

    # Add to lookups based on flags
    if exists_in_tm:
        if org_ref in mock_serviced_orgs:
            serviced_orgs[org_ref] = mock_serviced_orgs[org_ref]
        else:
            # Create a new one for test-specific refs
            serviced_orgs[org_ref] = TransmodelServicedOrganisations(
                name=f"Test Org {org_ref}",
                organisation_code=org_ref,
            )

    if exists_in_txc:
        if org_ref in mock_txc_serviced_orgs:
            txc_serviced_orgs[org_ref] = mock_txc_serviced_orgs[org_ref]
        else:
            # Create a new one for test-specific refs
            txc_serviced_orgs[org_ref] = TXCServicedOrganisation(
                OrganisationCode=org_ref,
                Name=f"Test Org {org_ref}",
                WorkingDays=[
                    TXCServicedOrganisationDatePattern(
                        StartDate=date(2023, 1, 1),
                        EndDate=date(2023, 12, 31),
                    )
                ],
            )

    result = process_org_ref(
        org_ref=org_ref,
        operating_on_working_days=operating_on_working_days,
        vehicle_journey=TransmodelVehicleJourneyFactory.create_with_id(100),
        serviced_orgs=serviced_orgs,
        txc_serviced_orgs=txc_serviced_orgs,
    )

    if expected_result == (None, []):
        assert result[0] is None
        assert result[1] == []
    else:
        assert result[0] is not None
        assert isinstance(result[0], TransmodelServicedOrganisationVehicleJourney)
        assert result[0].operating_on_working_days == operating_on_working_days

        if (
            exists_in_txc
            and org_ref in txc_serviced_orgs
            and txc_serviced_orgs[org_ref].WorkingDays
        ):
            assert len(result[1]) > 0
        else:
            assert result[1] == []


@pytest.mark.parametrize(
    "day_type_config, expected_counts",
    [
        pytest.param(None, (0, 0), id="None input returns empty lists"),
        pytest.param(
            {
                "DaysOfOperation": [{"WorkingDays": ["SCH"], "Holidays": ["Holiday1"]}],
                "DaysOfNonOperation": [],
            },
            (2, 2),
            id="DaysOfOperation only",
        ),
        pytest.param(
            {
                "DaysOfOperation": [],
                "DaysOfNonOperation": [{"WorkingDays": ["MVSERVLESS"], "Holidays": []}],
            },
            (1, 1),
            id="DaysOfNonOperation only",
        ),
        pytest.param(
            {
                "DaysOfOperation": [{"WorkingDays": ["SCH"], "Holidays": []}],
                "DaysOfNonOperation": [
                    {"WorkingDays": ["MVSERVLESS"], "Holidays": ["Holiday1"]}
                ],
            },
            (3, 3),
            id="Both operation and non-operation days",
        ),
        pytest.param(
            {
                "DaysOfOperation": [
                    {"WorkingDays": ["SCH"], "Holidays": []},
                    {"WorkingDays": [], "Holidays": ["Holiday1"]},
                ],
                "DaysOfNonOperation": [{"WorkingDays": ["MVSERVLESS"], "Holidays": []}],
            },
            (3, 3),
            id="Multiple elements in operation/non-operation lists",
        ),
    ],
)
def test_create_serviced_organisation_vehicle_journeys(
    day_type_config,
    expected_counts,
    mock_serviced_orgs,
    mock_txc_serviced_orgs,
):
    """Test creating serviced organisation vehicle journey records"""
    if day_type_config is None:
        serviced_org_day_type = None
    else:
        days_of_operation = []
        for day_op in day_type_config["DaysOfOperation"]:
            days_of_operation.append(
                TXCServicedOrganisationDays(
                    WorkingDays=day_op["WorkingDays"],
                    Holidays=day_op["Holidays"],
                )
            )

        days_of_non_operation = []
        for day_non_op in day_type_config["DaysOfNonOperation"]:
            days_of_non_operation.append(
                TXCServicedOrganisationDays(
                    WorkingDays=day_non_op["WorkingDays"],
                    Holidays=day_non_op["Holidays"],
                )
            )

        serviced_org_day_type = TXCServicedOrganisationDayType(
            DaysOfOperation=days_of_operation,
            DaysOfNonOperation=days_of_non_operation,
        )

    vj_records, working_patterns = create_serviced_organisation_vehicle_journeys(
        serviced_org_day_type=serviced_org_day_type,
        vehicle_journey=TransmodelVehicleJourneyFactory.create_with_id(100),
        serviced_orgs=mock_serviced_orgs,
        txc_serviced_orgs=mock_txc_serviced_orgs,
    )

    # Then
    assert len(vj_records) == expected_counts[0]
    assert len(working_patterns) == expected_counts[1]
