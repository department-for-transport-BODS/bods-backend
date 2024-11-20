from typing import List, Optional

from pti.models import Line, VehicleJourney
from timetables.transxchange import TransXChangeElement


class BaseValidator:
    def __init__(self, root):
        self.root = root
        self.namespaces = {"x": self.root.nsmap.get(None)}

        self._vehicle_journeys = None
        self._lines = None
        self._journey_patterns = None
        self._services = None

    @property
    def lines(self):
        if self._lines is not None:
            return self._lines
        lines = self.root.xpath("//x:Line", namespaces=self.namespaces)
        self._lines = [Line.from_xml(line) for line in lines]
        return self._lines

    @property
    def vehicle_journeys(self):
        if self._vehicle_journeys is not None:
            return self._vehicle_journeys
        xpath = "//x:VehicleJourneys/x:VehicleJourney"
        journeys = self.root.xpath(xpath, namespaces=self.namespaces)
        self._vehicle_journeys = [VehicleJourney.from_xml(vj) for vj in journeys]
        return self._vehicle_journeys

    @property
    def services(self):
        if self._services is not None:
            return self._services
        xpath = "//x:Services/x:Service"
        self._services = self.root.xpath(xpath, namespaces=self.namespaces)
        return self._services

    @property
    def journey_patterns(self):
        if self._journey_patterns is not None:
            return self._journey_patterns

        xpath = "//x:JourneyPatterns/x:JourneyPattern"
        patterns = self.root.xpath(xpath, namespaces=self.namespaces)
        self._journey_patterns = patterns
        return self._journey_patterns

    def get_journey_pattern_ref_by_vehicle_journey_code(self, code: str):
        vehicle_journeys = self.get_vehicle_journey_by_code(code)

        if len(vehicle_journeys) < 1:
            return ""

        vj = vehicle_journeys[0]
        if vj.journey_pattern_ref != "":
            return vj.journey_pattern_ref
        elif vj.vehicle_journey_ref != "":
            return self.get_journey_pattern_ref_by_vehicle_journey_code(vj.vehicle_journey_ref)
        else:
            return ""

    def get_journey_pattern_refs_by_line_ref(self, ref: str):
        """
        Returns all the JourneyPatternRefs that appear in the VehicleJourneys have
        LineRef equal to ref.
        """
        jp_refs = set()
        vehicle_journeys = self.get_vehicle_journey_by_line_ref(ref)
        for journey in vehicle_journeys:
            jp_ref = self.get_journey_pattern_ref_by_vehicle_journey_code(journey.code)
            if jp_ref != "":
                jp_refs.add(jp_ref)
        return list(jp_refs)

    def get_vehicle_journey_by_line_ref(self, ref) -> List[VehicleJourney]:
        """
        Get all the VehicleJourneys that have LineRef equal to ref.
        """
        return [vj for vj in self.vehicle_journeys if vj.line_ref == ref]

    def get_vehicle_journey_by_pattern_journey_ref(self, ref) -> List[VehicleJourney]:
        """
        Get all the VehicleJourneys that JourneyPatternRef equal to ref.
        """
        return [vj for vj in self.vehicle_journeys if vj.journey_pattern_ref == ref]

    def get_service_by_vehicle_journey(self, service_ref: str) -> Optional[TransXChangeElement]:
        """Find service for vehicle journey based on service ref

        Args:
            service_ref (str): Service ref from vehicle journey

        Returns:
            Optional[TransXChangeElement]: service element
        """
        for service in self.services:
            service_code = service.xpath("string(x:ServiceCode)", namespaces=self.namespaces)
            if service_code is not None and service_ref == service_code:
                return service
        return None

    def get_vehicle_journey_by_code(self, code) -> List[VehicleJourney]:
        """
        Get the VehicleJourney with VehicleJourneyCode equal to code.
        """
        return [vj for vj in self.vehicle_journeys if vj.code == code]

    def get_route_section_by_stop_point_ref(self, ref):
        xpath = (
            "//x:RouteSections/x:RouteSection/"
            f"x:RouteLink[string(x:From/x:StopPointRef) = '{ref}' "
            f"or string(x:To/x:StopPointRef) = '{ref}']/@id"
        )
        link_refs = self.root.xpath(xpath, namespaces=self.namespaces)
        return list(set(link_refs))

    def get_journey_pattern_section_refs_by_route_link_ref(self, ref):
        xpath = (
            "//x:JourneyPatternSections/x:JourneyPatternSection"
            f"[x:JourneyPatternTimingLink[string(x:RouteLinkRef) = '{ref}']]/@id"
        )
        section_refs = self.root.xpath(xpath, namespaces=self.namespaces)
        return list(set(section_refs))

    def get_journey_pattern_ref_by_journey_pattern_section_ref(self, ref):
        xpath = f"//x:JourneyPattern[string(x:JourneyPatternSectionRefs) = '{ref}']/@id"
        journey_pattern_refs = self.root.xpath(xpath, namespaces=self.namespaces)
        return list(set(journey_pattern_refs))

    def get_stop_point_ref_from_journey_pattern_ref(self, ref):
        xpath = f"//x:StandardService/x:JourneyPattern[@id='{ref}']" "/x:JourneyPatternSectionRefs/text()"
        section_refs = self.root.xpath(xpath, namespaces=self.namespaces)

        all_stop_refs = []
        for section_ref in section_refs:
            xpath = (
                "//x:JourneyPatternSections/x:JourneyPatternSection"
                f"[@id='{section_ref}']/x:JourneyPatternTimingLink/*"
                "[local-name() = 'From' or local-name() = 'To']/x:StopPointRef/text()"
            )
            stop_refs = self.root.xpath(xpath, namespaces=self.namespaces)
            all_stop_refs += stop_refs

        return list(set(all_stop_refs))

    def get_locality_name_from_annotated_stop_point_ref(self, ref) -> Optional[str]:
        """
        Get the LocalityName of an AnnotatedStopPointRef from its StopPointRef.
        """
        xpath = "//x:StopPoints//x:AnnotatedStopPointRef[string(x:StopPointRef)" f" = '{ref}']/x:LocalityName/text()"
        names = self.root.xpath(xpath, namespaces=self.namespaces)
        if names:
            return names[0]
        return None

