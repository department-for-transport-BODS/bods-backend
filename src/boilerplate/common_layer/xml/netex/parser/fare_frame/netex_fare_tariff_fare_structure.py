"""

fareStructureElements Parsing inside Tariff
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name
from ...models import (
    DistanceMatrixElement,
    FareStructureElement,
    FrequencyOfUse,
    GenericParameterAssignment,
    RoundTrip,
    UsageValidityPeriod,
    UserProfile,
    ValidityParameters,
    VersionedRef,
)
from ..data_objects.netex_profiles import parse_user_profile
from ..netex_types import (
    parse_activation_means_type,
    parse_usage_end_type,
    parse_usage_trigger_type,
)
from ..netex_utility import (
    get_netex_element,
    get_netex_text,
    parse_multilingual_string,
    parse_versioned_ref,
)

log = get_logger()


def parse_price_groups(elem: _Element) -> list[VersionedRef]:
    """
    Parse Price Groups
    """
    refs: list[VersionedRef] = []

    for child in elem:
        tag = get_tag_name(child)
        if tag == "PriceGroupRef":
            if (version := child.get("version")) and (ref := child.get("ref")):
                refs.append(VersionedRef(version=version, ref=ref))

    return refs


def parse_distance_matrix_element(elem: _Element) -> DistanceMatrixElement:
    """
    Parse DistanceMatrixElement inside distanceMatrixElements
    Inside FareStructureElement
    """
    element_id = elem.get("id")
    version = elem.get("version")

    if not element_id or not version:
        raise ValueError("Missing required id or version in DistanceMatrixElement")

    start_tariff_zone_ref = parse_versioned_ref(elem, "StartTariffZoneRef")
    end_tariff_zone_ref = parse_versioned_ref(elem, "EndTariffZoneRef")

    price_groups: list[VersionedRef] = []
    price_groups_elem = get_netex_element(elem, "priceGroups")
    if price_groups_elem is not None:
        price_groups = parse_price_groups(price_groups_elem)

    return DistanceMatrixElement(
        id=element_id,
        version=version,
        priceGroups=price_groups,
        StartTariffZoneRef=start_tariff_zone_ref,
        EndTariffZoneRef=end_tariff_zone_ref,
    )


def parse_usage_validity_period(elem: _Element) -> UsageValidityPeriod:
    """
    Parse UsageValidityPeriod in FareStructureElement.

    """

    period_id = elem.get("id")
    version = elem.get("version")

    if not period_id or not version:
        raise ValueError("Missing required id or version in UsageValidityPeriod")

    usage_trigger = parse_usage_trigger_type(elem)
    activation_means = parse_activation_means_type(elem)
    usage_end = parse_usage_end_type(elem)
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

    return RoundTrip(id=trip_id, version=version, TripType=trip_type)


def parse_validity_parameters(elem: _Element) -> ValidityParameters | None:
    """Parse ValidityParameters element."""
    line_ref = parse_versioned_ref(elem, "LineRef")

    if not line_ref:
        return None

    return ValidityParameters(LineRef=line_ref)


def parse_limitations(
    elem: _Element,
) -> list[UserProfile | RoundTrip | FrequencyOfUse | UsageValidityPeriod] | None:
    """Parse limitations element containing various limitation types."""
    limitations: list[
        UserProfile | RoundTrip | FrequencyOfUse | UsageValidityPeriod
    ] = []
    for limitation in elem:
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
                log.warning("Unknown limitation type", tag=limitation_tag)
        limitation.clear()

    return limitations if limitations else None


def parse_generic_parameter_assignment(elem: _Element) -> GenericParameterAssignment:
    """Parse GenericParameterAssignment element."""
    # Parse required attributes
    assignment_id = elem.get("id")
    version = elem.get("version")
    order = elem.get("order")

    if not assignment_id or not version or not order:
        raise ValueError("Missing required attributes in GenericParameterAssignment")

    # Parse required reference
    type_of_access_right_assignment_ref = parse_versioned_ref(
        elem, "TypeOfAccessRightAssignmentRef"
    )

    # Parse optional elements
    validity_parameter_assignment_type = None
    limitation_grouping_type = None
    validity_parameters = None
    limitations = None

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
                limitations = parse_limitations(child)

            case "TypeOfAccessRightAssignmentRef":
                # Already handled above
                pass
            case _:
                log.warning("Unknown GenericParameterAssignment tag", tag=tag)

    return GenericParameterAssignment(
        id=assignment_id,
        version=version,
        order=order,
        TypeOfAccessRightAssignmentRef=type_of_access_right_assignment_ref,
        ValidityParameterAssignmentType=validity_parameter_assignment_type,
        LimitationGroupingType=limitation_grouping_type,
        validityParameters=validity_parameters,
        limitations=limitations,
    )


def parse_fare_structure_element(elem: _Element) -> FareStructureElement:
    """
    Parse FareStructureElement element
    """
    element_id = elem.get("id")
    version = elem.get("version")

    if not element_id or not version:
        raise ValueError("Missing required id or version in FareStructureElement")

    name = parse_multilingual_string(elem, "Name")
    if name is None:
        name = get_netex_text(elem, "Name")

    type_of_fare_structure_element_ref = parse_versioned_ref(
        elem, "TypeOfFareStructureElementRef"
    )

    distance_matrix_elements: list[DistanceMatrixElement] = []
    generic_parameter_assignments: list[GenericParameterAssignment] = []

    for child in elem:
        tag = get_tag_name(child)
        match tag:
            case "distanceMatrixElements":
                for dme_child in child:
                    dme_tag = get_tag_name(dme_child)
                    if dme_tag == "DistanceMatrixElement":
                        distance_matrix_elements.append(
                            parse_distance_matrix_element(dme_child)
                        )
                    else:
                        log.warning("Unknown distanceMatrixElements tag", tag=dme_tag)
                    dme_child.clear()
            case "GenericParameterAssignment":
                generic_parameter_assignments.append(
                    parse_generic_parameter_assignment(child)
                )
            case "Name" | "TypeOfFareStructureElementRef":
                # Already handled
                pass
            case _:
                log.warning("Unknown FareStructureElement tag", tag=tag)
        child.clear()

    return FareStructureElement(
        id=element_id,
        version=version,
        Name=name,
        TypeOfFareStructureElementRef=type_of_fare_structure_element_ref,
        distanceMatrixElements=(
            distance_matrix_elements if distance_matrix_elements else None
        ),
        GenericParameterAssignment=(
            generic_parameter_assignments[0] if generic_parameter_assignments else None
        ),
    )
