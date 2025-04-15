"""
Validators related to stop points
"""

from dateutil import parser
from dateutil.relativedelta import relativedelta
from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ..utils.utils_xml import extract_text
from ..xml_elements import TransXChangeElement
from .base import BaseValidator

log = get_logger()


class StopPointValidator(BaseValidator):
    """
    Validate stop points
    """

    @property
    def stop_point_ref(self):
        """
        Get AtcoCode
        """
        xpath = "string(x:AtcoCode)"
        return self.root.xpath(xpath, namespaces=self.namespaces)

    def get_operating_profile_by_vehicle_journey_code(self, ref: str):
        """
        Get OperatingProfile elements by VehicleJourneyCode
        """
        xpath = (
            f"//x:VehicleJourney[string(x:VehicleJourneyCode) = '{ref}']"
            "//x:OperatingProfile"
        )
        profiles = self.root.xpath(xpath, namespaces=self.namespaces)
        return profiles

    def get_service_operating_period(self):
        """
        Get Service OperatingPeriod elements
        """
        xpath = "//x:Service//x:OperatingPeriod"
        periods = self.root.xpath(xpath, namespaces=self.namespaces)
        return periods

    def has_valid_operating_profile(self, ref: str) -> bool:
        """
        Check if operating profile is valid
        """
        profiles = self.get_operating_profile_by_vehicle_journey_code(ref)

        if len(profiles) < 1:
            return True
        profile = profiles[0]

        start_date = profile.xpath("string(.//x:StartDate)", namespaces=self.namespaces)
        end_date = profile.xpath("string(.//x:EndDate)", namespaces=self.namespaces)

        if start_date == "" or end_date == "":
            # If start or end date unspecified, inherit from the service's
            # OperatingPeriod
            periods = self.get_service_operating_period()
            if len(periods) > 0:
                period = periods[0]
                if start_date == "":
                    start_date = period.xpath(
                        "string(./x:StartDate)", namespaces=self.namespaces
                    )
                if end_date == "":
                    end_date = period.xpath(
                        "string(./x:EndDate)", namespaces=self.namespaces
                    )

        if start_date == "" or end_date == "":
            return False

        start_date = parser.parse(start_date)
        end_date = parser.parse(end_date)
        less_than_2_months = end_date <= start_date + relativedelta(months=2)
        return less_than_2_months

    def has_coach_as_service_mode(self, service: TransXChangeElement) -> bool:
        """Check whether service mode is coach or not

        Args:
            service (TransXChangeElement): service element of vj

        Returns:
            bool: True if service mode matches
        """
        mode: str = service.xpath("string(x:Mode)", namespaces=self.namespaces)
        if mode is not None and mode.lower() == "coach".lower():
            return True
        return False

    def validate(self):
        """
        Run validations

        Returns:
            bool: True if valid, False otherwise
        """
        route_link_refs = self.get_route_section_by_stop_point_ref(self.stop_point_ref)
        all_vj = []

        for link_ref in route_link_refs:
            section_refs = self.get_journey_pattern_section_refs_by_route_link_ref(
                link_ref
            )
            for section_ref in section_refs:
                jp_refs = self.get_journey_pattern_ref_by_journey_pattern_section_ref(
                    section_ref
                )
                for jp_ref in jp_refs:
                    jp_vjs = []
                    vehicle_journies = self.get_vehicle_journey_by_pattern_journey_ref(
                        jp_ref
                    )
                    for vj in vehicle_journies:
                        service = self.get_service_by_vehicle_journey(vj.service_ref)
                        if not (
                            service is not None
                            and self.has_coach_as_service_mode(service)
                        ):
                            jp_vjs.append(vj)

                    all_vj += jp_vjs

        for journey in all_vj:
            if not self.has_valid_operating_profile(journey.code):
                return False

        return True


def get_stop_point_ref_list(stop_points, ns) -> list[str]:
    """
    For each stop point in the input, the function looks for FlexibleStopUsage elements
    and extracts their StopPointRef values.
    """
    stop_point_ref_list: list[str] = []
    for flex_stop_point in stop_points:
        flexible_stop_usage_list = flex_stop_point.xpath(
            "x:FlexibleStopUsage", namespaces=ns
        )
        if len(flexible_stop_usage_list) > 0:
            for flexible_stop_usage in flexible_stop_usage_list:
                ref = extract_text(
                    flexible_stop_usage.xpath("x:StopPointRef", namespaces=ns), None
                )
                if ref is not None:
                    stop_point_ref_list.append(ref)
                else:
                    log.warning(
                        "Missing StopPointRef in FlexibleStopUsage",
                        flexible_stop_usage=flexible_stop_usage,
                    )

    return stop_point_ref_list


def validate_non_naptan_stop_points(_context, points: list[_Element]) -> bool:
    """
    Runs the StopPointValidator
    """
    log.info(
        "Validation Start: Non Naptan Stop Points",
    )
    point = points[0]
    validator = StopPointValidator(point)
    return validator.validate()
