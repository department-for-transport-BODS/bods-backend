"""
Serviced Organisation Loading
"""

from common_layer.database import SqlDB
from common_layer.database.models import TransmodelServicedOrganisations
from common_layer.database.repos import TransmodelServicedOrganisationsRepo
from common_layer.txc.models import TXCServicedOrganisation
from structlog.stdlib import get_logger

from ..helpers import ServicedOrgLookup

log = get_logger()


def convert_txc_to_transmodel_org(
    txc_org: TXCServicedOrganisation,
) -> TransmodelServicedOrganisations:
    """Convert TXC Pydantic model to SQLAlchemy model"""
    return TransmodelServicedOrganisations(
        name=txc_org.Name, organisation_code=txc_org.OrganisationCode
    )


def get_org_name_code_pairs(
    txc_orgs: list[TXCServicedOrganisation],
) -> list[tuple[str | None, str]]:
    """Extract name and organisation code pairs from TXC organizations"""
    return [(org.Name, org.OrganisationCode) for org in txc_orgs]


def filter_new_organizations(
    txc_orgs: list[TXCServicedOrganisation],
    existing_pairs: set[tuple[str | None, str | None]],
) -> list[TransmodelServicedOrganisations]:
    """
    Filter out organizations that already exist
    convert new ones to TransmodelServicedOrganisations
    """
    return [
        convert_txc_to_transmodel_org(org)
        for org in txc_orgs
        if (org.Name, org.OrganisationCode) not in existing_pairs
    ]


def get_existing_pairs(
    existing_orgs: list[TransmodelServicedOrganisations],
) -> set[tuple[str | None, str | None]]:
    """Create a set of existing (name, organisation_code) pairs"""
    return {(org.name, org.organisation_code) for org in existing_orgs}


def create_serviced_org_mapping(
    created_orgs: list[TransmodelServicedOrganisations],
    existing_orgs: list[TransmodelServicedOrganisations],
) -> ServicedOrgLookup:
    """
    Create a mapping of organisation_code to TransmodelServicedOrganisations
    from both created and existing organizations.

    Returns: dict[organisation_code, SQLAlchemy Dataclass for transmodel_servicedorganisations]
    """
    all_orgs: list[TransmodelServicedOrganisations] = [*created_orgs, *existing_orgs]

    org_mapping: ServicedOrgLookup = {}

    for org in all_orgs:
        if org.organisation_code is None:
            raise ValueError(f"Organisation {org.name} has no organisation_code")

        if org.organisation_code in org_mapping:
            raise ValueError(
                f"Duplicate organisation_code found: {org.organisation_code}"
            )

        org_mapping[org.organisation_code] = org

    return org_mapping


def load_serviced_organizations(
    txc_orgs: list[TXCServicedOrganisation],
    db: SqlDB,
) -> ServicedOrgLookup:
    """
    Load serviced organizations into database

    The Serviced Organisations need to be unique, but there aren't constraints in the DB
    So first we try fetching the existing orgs that exist
    And then insert the new ones into the db
    """
    if not txc_orgs:
        return {}

    repo = TransmodelServicedOrganisationsRepo(db)

    org_pairs = get_org_name_code_pairs(txc_orgs)
    existing_orgs = repo.get_existing_by_name_and_code(org_pairs)
    existing_pairs = get_existing_pairs(existing_orgs)

    new_orgs = filter_new_organizations(txc_orgs, existing_pairs)
    created_orgs = repo.bulk_insert(new_orgs) if new_orgs else []
    mapping = create_serviced_org_mapping(created_orgs, existing_orgs)
    log.info(
        "Serviced Organisations Loaded",
        existing_count=len(existing_orgs),
        created_count=len(created_orgs),
        orgs=mapping,
    )
    return mapping
