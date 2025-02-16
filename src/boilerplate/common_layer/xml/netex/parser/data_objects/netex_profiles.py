"""
FareFrame
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...models import CompanionProfile, UserProfile
from ..netex_types import parse_discount_basis_type, parse_proof_of_identity_type
from ..netex_utility import (
    get_netex_element,
    get_netex_int,
    parse_multilingual_string,
    parse_versioned_ref,
)

log = get_logger()


def parse_companion_profile(elem: _Element) -> CompanionProfile:
    """Parse CompanionProfile element."""
    user_profile_ref = parse_versioned_ref(elem, "UserProfileRef")
    min_persons = get_netex_int(elem, "MinimumNumberOfPersons")
    max_persons = get_netex_int(elem, "MaximumNumberOfPersons")
    discount_basis = parse_discount_basis_type(elem)

    profile_id = elem.get("id")
    version = elem.get("version")

    if not profile_id or not version:
        raise ValueError("Missing required id or version in CompanionProfile")

    return CompanionProfile(
        id=profile_id,
        version=version,
        UserProfileRef=user_profile_ref,
        MinimumNumberOfPersons=min_persons,
        MaximumNumberOfPersons=max_persons,
        DiscountBasis=discount_basis,
    )


def parse_companion_profiles(elem: _Element) -> list[CompanionProfile]:
    """
    Parse comparionProfiles
    """
    profiles: list[CompanionProfile] = []
    for profile in elem:
        profiles.append(parse_companion_profile(profile))

    return profiles


def parse_user_profile(elem: _Element) -> UserProfile:
    """Parse UserProfile element."""
    name = parse_multilingual_string(elem, "Name")
    description = parse_multilingual_string(elem, "Description")
    type_of_concession_ref = parse_versioned_ref(elem, "TypeOfConcessionRef")
    min_age = get_netex_int(elem, "MinimumAge")
    max_age = get_netex_int(elem, "MaximumAge")
    proof_required = parse_proof_of_identity_type(elem, "ProofRequired")
    discount_basis = parse_discount_basis_type(elem)
    companion_profiles: list[CompanionProfile] = []
    companion_profile_elem = get_netex_element(elem, "companionProfiles")
    if companion_profile_elem is not None:
        companion_profiles = parse_companion_profiles(companion_profile_elem)
    profile_id = elem.get("id")
    version = elem.get("version")

    if not profile_id or not version:
        raise ValueError("Missing required id or version in UserProfile")

    if not name:
        raise ValueError("Missing Name")

    return UserProfile(
        id=profile_id,
        version=version,
        Name=name,
        Description=description,
        TypeOfConcessionRef=type_of_concession_ref,
        MinimumAge=min_age,
        MaximumAge=max_age,
        ProofRequired=proof_required,
        DiscountBasis=discount_basis,
        companionProfiles=companion_profiles if companion_profiles else None,
    )
