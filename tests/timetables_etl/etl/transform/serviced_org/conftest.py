"""
Serviced Org Conftest
"""

from datetime import date

import pytest
from common_layer.database.models import TransmodelServicedOrganisations
from common_layer.xml.txc.models import (
    TXCServicedOrganisation,
    TXCServicedOrganisationDatePattern,
)


@pytest.fixture(name="mock_serviced_orgs")
def serviced_org_dict() -> dict[str, TransmodelServicedOrganisations]:
    """
    Mocked ServiceOrgsLookup
    """
    orgs = {
        "SCH": TransmodelServicedOrganisations(
            name="School Days",
            organisation_code="SCH",
        ),
        "MVSERVLESS": TransmodelServicedOrganisations(
            name="MICHAEL SERVERLESS",
            organisation_code="MVSERVLESS",
        ),
        "Holiday1": TransmodelServicedOrganisations(
            name="Holiday Service",
            organisation_code="Holiday1",
        ),
    }
    # Simulate IDs being assigned
    for i, org in enumerate(orgs.values(), 1):
        org.id = i
    return orgs


@pytest.fixture(name="mock_txc_serviced_orgs")
def txc_serviced_orgs_dict() -> dict[str, TXCServicedOrganisation]:
    """
    Create TXC serviced organizations with date patterns
    """
    return {
        "SCH": TXCServicedOrganisation(
            OrganisationCode="SCH",
            Name="School Days",
            WorkingDays=[
                TXCServicedOrganisationDatePattern(
                    StartDate=date(2021, 8, 31),
                    EndDate=date(2025, 10, 22),
                )
            ],
        ),
        "MVSERVLESS": TXCServicedOrganisation(
            OrganisationCode="MVSERVLESS",
            Name="MICHAEL SERVERLESS",
            WorkingDays=[
                TXCServicedOrganisationDatePattern(
                    StartDate=date(2024, 8, 24),
                    EndDate=date(2026, 8, 24),
                )
            ],
        ),
        "Holiday1": TXCServicedOrganisation(
            OrganisationCode="Holiday1",
            Name="Holiday Service",
            WorkingDays=[
                TXCServicedOrganisationDatePattern(
                    StartDate=date(2023, 12, 24),
                    EndDate=date(2024, 1, 5),
                )
            ],
        ),
    }
