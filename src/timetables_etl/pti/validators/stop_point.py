from dateutil import parser
from pti.constants import MODE_COACH
from pti.validators.base import BaseValidator
from dateutil.relativedelta import relativedelta

from timetables.transxchange import TransXChangeElement

class StopPointValidator(BaseValidator):
    @property
    def stop_point_ref(self):
        xpath = "string(x:AtcoCode)"
        return self.root.xpath(xpath, namespaces=self.namespaces)

    def get_operating_profile_by_vehicle_journey_code(self, ref):
        xpath = f"//x:VehicleJourney[string(x:VehicleJourneyCode) = '{ref}']" "//x:OperatingProfile"
        profiles = self.root.xpath(xpath, namespaces=self.namespaces)
        return profiles

    def get_service_operating_period(self):
        xpath = "//x:Service//x:OperatingPeriod"
        periods = self.root.xpath(xpath, namespaces=self.namespaces)
        return periods

    def has_valid_operating_profile(self, ref):
        profiles = self.get_operating_profile_by_vehicle_journey_code(ref)

        if len(profiles) < 1:
            return True
        else:
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
                    start_date = period.xpath("string(./x:StartDate)", namespaces=self.namespaces)
                if end_date == "":
                    end_date = period.xpath("string(./x:EndDate)", namespaces=self.namespaces)

        if start_date == "" or end_date == "":
            return False

        start_date = parser.parse(start_date)
        end_date = parser.parse(end_date)
        less_than_2_months = end_date <= start_date + relativedelta(months=2)
        return less_than_2_months

    def has_coach_as_service_mode(self, service: TransXChangeElement) -> bool:
        """Check weather service mode is coach or not

        Args:
            service (TransXChangeElement): service element of vj

        Returns:
            bool: True if service mode matches
        """
        mode = service.xpath("string(x:Mode)", namespaces=self.namespaces)
        if mode is not None and mode.lower() == MODE_COACH.lower():
            return True
        return False

    def validate(self):
        route_link_refs = self.get_route_section_by_stop_point_ref(self.stop_point_ref)
        all_vj = []

        for link_ref in route_link_refs:
            section_refs = self.get_journey_pattern_section_refs_by_route_link_ref(link_ref)
            for section_ref in section_refs:
                jp_refs = self.get_journey_pattern_ref_by_journey_pattern_section_ref(section_ref)
                for jp_ref in jp_refs:
                    jp_vjs = []
                    vehicle_journies = self.get_vehicle_journey_by_pattern_journey_ref(jp_ref)
                    for vj in vehicle_journies:
                        service = self.get_service_by_vehicle_journey(vj.service_ref)
                        if not (service is not None and self.has_coach_as_service_mode(service)):
                            jp_vjs.append(vj)

                    all_vj += jp_vjs

        for journey in all_vj:
            if not self.has_valid_operating_profile(journey.code):
                return False

        return True
