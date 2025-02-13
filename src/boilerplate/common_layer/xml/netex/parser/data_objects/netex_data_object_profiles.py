"""
FareFrame
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name
from ...models import CompanionProfile, UserProfile
from ..netex_utility import parse_multilingual_string, parse_versioned_ref

log = get_logger()


def parse_companion_profile(elem: _Element) -> CompanionProfile:
    """Parse CompanionProfile element."""
    user_profile_ref = None
    min_persons = None
    max_persons = None
    discount_basis = None

    profile_id = elem.get("id")
    version = elem.get("version")

    if not profile_id or not version:
        raise ValueError("Missing required id or version in CompanionProfile")

    for child in elem:
        tag = get_tag_name(child)
        match tag:
            case "UserProfileRef":
                user_profile_ref = parse_versioned_ref(child)
            case "MinimumNumberOfPersons":
                min_persons = int(child.text) if child.text else None
            case "MaximumNumberOfPersons":
                max_persons = int(child.text) if child.text else None
            case "DiscountBasis":
                discount_basis = child.text
            case _:
                log.warning("Unknown CompanionProfile tag", tag=tag)
        child.clear()

    if not all([user_profile_ref, min_persons is not None, max_persons is not None]):
        raise ValueError("Missing required fields in CompanionProfile")

    return CompanionProfile(
        id=profile_id,
        version=version,
        UserProfileRef=user_profile_ref,
        MinimumNumberOfPersons=min_persons,
        MaximumNumberOfPersons=max_persons,
        DiscountBasis=discount_basis,
    )


def parse_user_profile(elem: _Element) -> UserProfile:
    """Parse UserProfile element."""
    name = None
    description = None
    type_of_concession_ref = None
    min_age = None
    max_age = None
    proof_required = None
    discount_basis = None
    companion_profiles: list[CompanionProfile] = []

    # Get id and version from attributes
    profile_id = elem.get("id")
    version = elem.get("version")

    if not profile_id or not version:
        raise ValueError("Missing required id or version in UserProfile")

    for child in elem:
        tag = get_tag_name(child)
        match tag:
            case "Name":
                # Handle both MultilingualString and plain string
                if child.get("lang") or child.get("textIdType"):
                    name = parse_multilingual_string(child)
                else:
                    name = child.text
            case "Description":
                if child.get("lang") or child.get("textIdType"):
                    description = parse_multilingual_string(child)
                else:
                    description = child.text
            case "TypeOfConcessionRef":
                type_of_concession_ref = parse_versioned_ref(child)
            case "MinimumAge":
                min_age = int(child.text) if child.text else None
            case "MaximumAge":
                max_age = int(child.text) if child.text else None
            case "ProofRequired":
                proof_required = child.text
            case "DiscountBasis":
                discount_basis = child.text
            case "companionProfiles":
                for companion_elem in child:
                    if get_tag_name(companion_elem) == "CompanionProfile":
                        companion_profiles.append(
                            parse_companion_profile(companion_elem)
                        )
            case _:
                log.warning("Unknown UserProfile tag", tag=tag)
        child.clear()

    if not name:
        raise ValueError("Missing Name")
    if not type_of_concession_ref:
        raise ValueError("Missing TypeOfConcessionRef")
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
