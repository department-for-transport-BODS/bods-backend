"""

fareStructureElements Parsing inside Tariff
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name
from ...models import (
    DistanceMatrixElement,
    FrequencyOfUse,
    GenericParameterAssignment,
    RoundTrip,
    UsageValidityPeriod,
    UserProfile,
    ValidityParameters,
    VersionedRef,
)
from ..netex_utility import parse_versioned_ref
from .netex_profiles import parse_user_profile

log = get_logger()


def parse_distance_matrix_element(elem: _Element) -> DistanceMatrixElement:
    """Parse DistanceMatrixElement element."""
    price_groups: list[VersionedRef] = []
    start_tariff_zone_ref = None
    end_tariff_zone_ref = None

    # Get id and version from attributes
    element_id = elem.get("id")
    version = elem.get("version")

    if not element_id or not version:
        raise ValueError("Missing required id or version in DistanceMatrixElement")

    for child in elem:
        tag = get_tag_name(child)
        match tag:
            case "priceGroups":
                for price_group in child:
                    if get_tag_name(price_group) == "PriceGroupRef":
                        ref = price_group.get("ref")
                        version = price_group.get("version") or price_group.get(
                            "versionRef"
                        )
                        if ref and version:
                            price_groups.append(VersionedRef(ref=ref, version=version))
            case "StartTariffZoneRef":
                ref = child.get("ref")
                version = child.get("version") or child.get("versionRef")
                if ref and version:
                    start_tariff_zone_ref = VersionedRef(ref=ref, version=version)
            case "EndTariffZoneRef":
                ref = child.get("ref")
                version = child.get("version") or child.get("versionRef")
                if ref and version:
                    end_tariff_zone_ref = VersionedRef(ref=ref, version=version)
            case _:
                log.warning("Unknown DistanceMatrixElement tag", tag=tag)
        child.clear()

    if not price_groups:
        raise ValueError("Missing required priceGroups in DistanceMatrixElement")

    return DistanceMatrixElement(
        id=element_id,
        version=version,
        priceGroups=price_groups,
        StartTariffZoneRef=start_tariff_zone_ref,
        EndTariffZoneRef=end_tariff_zone_ref,
    )


def parse_usage_validity_period(elem: _Element) -> UsageValidityPeriod:
    """Parse UsageValidityPeriod element."""
    usage_trigger = None
    usage_end = None
    activation_means = None

    # Get required attributes
    period_id = elem.get("id")
    version = elem.get("version")

    if not period_id or not version:
        raise ValueError("Missing required id or version in UsageValidityPeriod")

    for child in elem:
        tag = get_tag_name(child)
        match tag:
            case "UsageTrigger":
                usage_trigger = child.text
            case "UsageEnd":
                usage_end = child.text
            case "ActivationMeans":
                activation_means = child.text
            case _:
                log.warning("Unknown UsageValidityPeriod tag", tag=tag)
        child.clear()

    if not usage_trigger or not usage_end or not activation_means:
        raise ValueError("Missing required fields in UsageValidityPeriod")

    return UsageValidityPeriod(
        id=period_id,
        version=version,
        UsageTrigger=usage_trigger,
        UsageEnd=usage_end,
        ActivationMeans=activation_means,
    )


def parse_frequency_of_use(elem: _Element) -> FrequencyOfUse:
    """Parse FrequencyOfUse element."""
    frequency_type = None

    # Get required attributes
    frequency_id = elem.get("id")
    version = elem.get("version")

    if not frequency_id or not version:
        raise ValueError("Missing required id or version in FrequencyOfUse")

    for child in elem:
        tag = get_tag_name(child)
        match tag:
            case "FrequencyOfUseType":
                frequency_type = child.text
            case _:
                log.warning("Unknown FrequencyOfUse tag", tag=tag)
        child.clear()

    if not frequency_type:
        raise ValueError("Missing required FrequencyOfUseType in FrequencyOfUse")

    return FrequencyOfUse(
        id=frequency_id, version=version, FrequencyOfUseType=frequency_type
    )


def parse_round_trip(elem: _Element) -> RoundTrip:
    """Parse RoundTrip element."""
    trip_type = None

    # Get required attributes
    trip_id = elem.get("id")
    version = elem.get("version")
    if not trip_id or not version:
        raise ValueError("Missing required id or version in RoundTrip")

    for child in elem:
        tag = get_tag_name(child)
        match tag:
            case "TripType":
                trip_type = child.text
            case _:
                log.warning("Unknown RoundTrip tag", tag=tag)
        child.clear()

    if not trip_type:
        raise ValueError("Missing required TripType in RoundTrip")

    return RoundTrip(id=trip_id, version=version, TripType=trip_type)


def parse_validity_parameters(elem: _Element) -> ValidityParameters:
    """Parse ValidityParameters element."""
    line_ref = parse_versioned_ref(elem, "LineRef")

    if not line_ref:
        raise ValueError("Missing required LineRef in ValidityParameters")

    return ValidityParameters(LineRef=line_ref)


def parse_generic_parameter_assignment(elem: _Element) -> GenericParameterAssignment:
    """Parse GenericParameterAssignment element."""
    type_of_access_right_assignment_ref = parse_versioned_ref(
        elem, "TypeOfAccessRightAssignmentRef"
    )
    validity_parameter_assignment_type = None
    limitation_grouping_type = None
    validity_parameters = None
    limitations: list[
        UserProfile | RoundTrip | FrequencyOfUse | UsageValidityPeriod
    ] = []

    # Get required attributes
    assignment_id = elem.get("id")
    version = elem.get("version")
    order = elem.get("order")

    if not assignment_id or not version or not order:
        raise ValueError("Missing required attributes in GenericParameterAssignment")
    for child in elem:
        tag = get_tag_name(child)
        match tag:

            case "ValidityParameterAssignmentType":
                validity_parameter_assignment_type = child.text
            case "LimitationGroupingType":
                limitation_grouping_type = child.text
            case "validityParameters":
                validity_parameters = parse_validity_parameters(child)
            case "limitations":
                for limitation in child:
                    limitation_tag = get_tag_name(limitation)
                    match limitation_tag:
                        case None:
                            # Limitation Tag Not Found
                            pass
                        case "UserProfile":
                            limitations.append(parse_user_profile(limitation))
                        case "RoundTrip":
                            limitations.append(parse_round_trip(limitation))
                        case "FrequencyOfUse":
                            limitations.append(parse_frequency_of_use(limitation))
                        case "UsageValidityPeriod":
                            limitations.append(parse_usage_validity_period(limitation))
                        case _:
                            log.warning("Unknown Limitation Tag")
            case _:
                log.warning("Unknown GenericParameterAssignment tag", tag=tag)
        child.clear()

    if not type_of_access_right_assignment_ref:
        raise ValueError(
            "Missing required TypeOfAccessRightAssignmentRef in GenericParameterAssignment"
        )

    return GenericParameterAssignment(
        id=assignment_id,
        version=version,
        order=order,
        TypeOfAccessRightAssignmentRef=type_of_access_right_assignment_ref,
        ValidityParameterAssignmentType=validity_parameter_assignment_type,
        LimitationGroupingType=limitation_grouping_type,
        validityParameters=validity_parameters,
        limitations=limitations if limitations else None,
    )
