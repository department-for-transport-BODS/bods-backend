"""
BaseValidator
"""

from typing import Optional

from common_layer.timetables.transxchange import TransXChangeElement
from lxml.etree import _Element  # type: ignore

from ..models.models_pti import Line, VehicleJourney


class BaseValidator:
    """
    Parent class for LinesValidator and StopPointValidator
    """

    def __init__(self, root: _Element):
        self.root = root
        ns = self.root.nsmap.get(None)
        self.namespaces: dict[str, str] | None = {"x": ns} if ns else None

        self._vehicle_journeys: list[VehicleJourney] | None = None
        self._lines: list[Line] | None = None
        self._journey_patterns = None
        self._services = None
        self._indexes: Optional[dict[str, dict[str, list[str]]]] = None

    def _build_indexes(self):
        if self._indexes is None:
            self._indexes = {
                "section_to_stop_refs": self._index_jp_sections(),
                "jp_to_section_refs": self._index_journey_patterns(),
            }

    @property
    def lines(self) -> list[Line]:
        """
        Gets and caches all Line elements
        """
        if self._lines is not None:
            return self._lines
        lines = self.root.xpath("//x:Line", namespaces=self.namespaces)
        self._lines = [Line.from_xml(line) for line in lines]
        return self._lines

    @property
    def vehicle_journeys(self) -> list[VehicleJourney]:
        """
        Gets and caches all VehicleJourney elements
        """
        if self._vehicle_journeys is not None:
            return self._vehicle_journeys
        xpath = "//x:VehicleJourneys/x:VehicleJourney"
        journeys = self.root.xpath(xpath, namespaces=self.namespaces)
        self._vehicle_journeys = [VehicleJourney.from_xml(vj) for vj in journeys]
        return self._vehicle_journeys

    @property
    def services(self):
        """
        Gets and caches all Service elements
        """
        if self._services is not None:
            return self._services
        xpath = "//x:Services/x:Service"
        self._services = self.root.xpath(xpath, namespaces=self.namespaces)
        return self._services

    @property
    def journey_patterns(self):
        """
        Gets and caches all JourneyPattern elements
        """
        if self._journey_patterns is not None:
            return self._journey_patterns

        xpath = "//x:JourneyPatterns/x:JourneyPattern"
        patterns = self.root.xpath(xpath, namespaces=self.namespaces)
        self._journey_patterns = patterns
        return self._journey_patterns

    def get_journey_pattern_ref_by_vehicle_journey_code(self, code: str) -> str:
        """
        Retrieves the journey pattern reference for a given vehicle journey code.
        If the VJ references another VJ, recursively follows the reference chain.
        """
        vehicle_journeys = self.get_vehicle_journey_by_code(code)

        if len(vehicle_journeys) < 1:
            return ""

        vj = vehicle_journeys[0]
        if vj.journey_pattern_ref != "":
            return vj.journey_pattern_ref
        if vj.vehicle_journey_ref != "":
            return self.get_journey_pattern_ref_by_vehicle_journey_code(
                vj.vehicle_journey_ref
            )
        return ""

    def get_journey_pattern_refs_by_line_ref(self, ref: str) -> list[str]:
        """
        Returns all the JourneyPatternRefs that appear in the VehicleJourneys have
        LineRef equal to ref.
        """
        jp_refs: set[str] = set()
        vehicle_journeys = self.get_vehicle_journey_by_line_ref(ref)
        for journey in vehicle_journeys:
            jp_ref = self.get_journey_pattern_ref_by_vehicle_journey_code(journey.code)
            if jp_ref != "":
                jp_refs.add(jp_ref)
        return list(jp_refs)

    def get_vehicle_journey_by_line_ref(self, ref: str) -> list[VehicleJourney]:
        """
        Get all the VehicleJourneys that have LineRef equal to ref.
        """
        return [vj for vj in self.vehicle_journeys if vj.line_ref == ref]

    def get_vehicle_journey_by_pattern_journey_ref(
        self, ref: str
    ) -> list[VehicleJourney]:
        """
        Get all the VehicleJourneys that JourneyPatternRef equal to ref.
        """
        return [vj for vj in self.vehicle_journeys if vj.journey_pattern_ref == ref]

    def get_service_by_vehicle_journey(
        self, service_ref: str
    ) -> TransXChangeElement | None:
        """Find service for vehicle journey based on service ref

        Args:
            service_ref (str): Service ref from vehicle journey

        Returns:
            Optional[TransXChangeElement]: service element
        """
        for service in self.services:
            service_code = service.xpath(
                "string(x:ServiceCode)", namespaces=self.namespaces
            )
            if service_code is not None and service_ref == service_code:
                return service
        return None

    def get_vehicle_journey_by_code(self, code: str) -> list[VehicleJourney]:
        """
        Get all VehicleJourneys with matching VehicleJourneyCode
        """
        return [vj for vj in self.vehicle_journeys if vj.code == code]

    def get_route_section_by_stop_point_ref(self, ref: str) -> list[str]:
        """
        Finds all route link IDs with a specific stop point reference
        Either as origin or destination.
        """
        xpath = (
            "//x:RouteSections/x:RouteSection/"
            f"x:RouteLink[string(x:From/x:StopPointRef) = '{ref}' "
            f"or string(x:To/x:StopPointRef) = '{ref}']/@id"
        )
        link_refs = self.root.xpath(xpath, namespaces=self.namespaces)
        return list(set(link_refs))

    def get_journey_pattern_section_refs_by_route_link_ref(self, ref: str) -> list[str]:
        """
        Finds journey pattern section IDs that contain a specific route link reference.
        """
        xpath = (
            "//x:JourneyPatternSections/x:JourneyPatternSection"
            f"[x:JourneyPatternTimingLink[string(x:RouteLinkRef) = '{ref}']]/@id"
        )
        section_refs = self.root.xpath(xpath, namespaces=self.namespaces)
        return list(set(section_refs))

    def get_journey_pattern_ref_by_journey_pattern_section_ref(
        self, ref: str
    ) -> list[str]:
        """
        Finds journey pattern IDs that contain a specific journey pattern section reference.
        """
        xpath = f"//x:JourneyPattern[string(x:JourneyPatternSectionRefs) = '{ref}']/@id"
        journey_pattern_refs = self.root.xpath(xpath, namespaces=self.namespaces)
        return list(set(journey_pattern_refs))

    def _index_jp_sections(self) -> dict[str, list[str]]:
        """
        Build a map from JourneyPatternSection ID to all stop point refs used in its timing links.
        """
        section_to_stop_refs: dict[str, list[str]] = {}
        sections = self.root.xpath(
            "//x:JourneyPatternSections/x:JourneyPatternSection",
            namespaces=self.namespaces,
        )
        for section in sections:
            section_id = section.get("id")
            stop_refs = section.xpath(
                "./x:JourneyPatternTimingLink/*[local-name()='From' or local-name()='To']"
                "/x:StopPointRef/text()",
                namespaces=self.namespaces,
            )
            section_to_stop_refs[section_id] = stop_refs
        return section_to_stop_refs

    def _index_journey_patterns(self) -> dict[str, list[str]]:
        """
        Build a map from JourneyPattern ID to its list of JourneyPatternSectionRefs.
        """
        jp_to_section_refs: dict[str, list[str]] = {}
        journey_patterns = self.root.xpath(
            "//x:StandardService/x:JourneyPattern", namespaces=self.namespaces
        )
        for jp in journey_patterns:
            jp_id = jp.get("id")
            section_refs = jp.xpath(
                "./x:JourneyPatternSectionRefs/text()", namespaces=self.namespaces
            )
            jp_to_section_refs[jp_id] = section_refs
        return jp_to_section_refs

    def get_stop_point_ref_from_journey_pattern_ref(self, ref: str) -> list[str]:
        """
        Quickly get all unique stop points for a journey pattern by looking up prebuilt indexes.
        """
        self._build_indexes()  # build once if needed
        if self._indexes is None:
            raise ValueError("No index found after building indexes")

        all_stop_refs: list[str] = []
        for section_ref in self._indexes["jp_to_section_refs"].get(ref, []):
            all_stop_refs.extend(
                self._indexes["section_to_stop_refs"].get(section_ref, [])
            )
        return list(set(all_stop_refs))
