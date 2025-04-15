"""
PTI Flexible Service Validation
"""

from typing import Callable

from common_layer.database.client import SqlDB
from common_layer.database.repos import NaptanStopPointRepo
from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...constants import NAMESPACE
from ...utils.utils_xml import extract_text
from ..stop_point import get_stop_point_ref_list

log = get_logger()


def check_flexible_service_timing_status(
    _: _Element | None, flexiblejourneypatterns: list[_Element]
) -> bool:
    """
    Examines XML journey pattern data and verifies that in cases where
    both fixed and flexible stops are present in the same sequence, all fixed stops
    have a timing status of "otherPoint".
    """
    log.info(
        "Validation Start: Flexible Service Timing Status",
    )
    timing_status_value_list: list[str | None] = []
    flexiblejourneypattern = flexiblejourneypatterns[0]
    stop_points_in_seq_list = flexiblejourneypattern.xpath(
        "x:StopPointsInSequence", namespaces=NAMESPACE
    )
    for stop_points_in_seq in stop_points_in_seq_list:
        fixed_stop_usage_list = stop_points_in_seq.xpath(
            "x:FixedStopUsage", namespaces=NAMESPACE
        )
        flexible_stop_usage_list = stop_points_in_seq.xpath(
            "x:FlexibleStopUsage", namespaces=NAMESPACE
        )

        if len(fixed_stop_usage_list) > 0 and len(flexible_stop_usage_list) > 0:
            for fixed_stop_usage in fixed_stop_usage_list:
                timing_status_value_list.append(
                    extract_text(
                        fixed_stop_usage.xpath("x:TimingStatus", namespaces=NAMESPACE),
                        "",
                    )
                )

    result = all(
        timing_status_value == "otherPoint"
        for timing_status_value in timing_status_value_list
    )
    return result


def get_flexible_service_stop_point_ref_validator(
    db: SqlDB,
) -> Callable[[_Element | None, list[_Element]], bool]:
    """
    Creates a validator function that checks if all flexible service stop points are
    properly registered in the NAPTAN database as flexible bus stops.
    """

    def check_flexible_service_stop_point_ref(
        _: _Element | None, flexiblejourneypatterns: list[_Element]
    ) -> bool:
        log.info(
            "Validation Start: Check Flexible Service Stop Point Ref",
        )
        atco_codes_list: list[str] = []
        flexiblejourneypattern = flexiblejourneypatterns[0]
        stop_points_in_seq_list = flexiblejourneypattern.xpath(
            "x:StopPointsInSequence", namespaces=NAMESPACE
        )
        stop_points_in_flexzone_list = flexiblejourneypattern.xpath(
            "x:FlexibleZones", namespaces=NAMESPACE
        )
        atco_codes_list = list(
            set(
                get_stop_point_ref_list(stop_points_in_seq_list)
                + get_stop_point_ref_list(stop_points_in_flexzone_list)
            )
        )
        repo = NaptanStopPointRepo(db)
        total_compliant = repo.get_count(
            atco_codes=atco_codes_list, bus_stop_type="FLX", stop_type="BCT"
        )

        return total_compliant == len(atco_codes_list)

    return check_flexible_service_stop_point_ref


def has_flexible_service_classification(
    _: _Element | None, services: list[_Element]
) -> bool:
    """
    Check when file has detected a flexible service (includes
    FlexibleService), it has ServiceClassification and Flexible elements.
    If the file also has a standard service, then return True.
    """
    log.info(
        "Validation Start: Has Flexible Service Classification",
    )
    for service in services:
        flexible_service_list = service.xpath("x:FlexibleService", namespaces=NAMESPACE)

        if not flexible_service_list:
            return True

        service_classification_list = service.xpath(
            "x:ServiceClassification", namespaces=NAMESPACE
        )
        if not service_classification_list:
            return False

        for service_classification in service_classification_list:
            if service_classification.xpath("x:Flexible", namespaces=NAMESPACE):
                return True

        return False
    return False


def check_flexible_service_times(
    _: _Element | None, vehiclejourneys: list[_Element]
) -> bool:
    """
    Check when FlexibleVehicleJourney is present, that FlexibleServiceTimes
    is also present at least once. If not present at all, then return False.
    """
    log.info(
        "Validation Start: Check Flexible Service Times",
    )
    flexible_vehiclejourneys = vehiclejourneys[0].xpath(
        "x:FlexibleVehicleJourney", namespaces=NAMESPACE
    )
    if flexible_vehiclejourneys:
        for flexible_journey in flexible_vehiclejourneys:
            flexible_service_times = flexible_journey.xpath(
                "x:FlexibleServiceTimes", namespaces=NAMESPACE
            )
            if len(flexible_service_times) == 0:
                return False

            return True
    return False
