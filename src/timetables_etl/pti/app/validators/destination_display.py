"""
DestinationDisplay PTI Validator
"""

from lxml.etree import _Element
from structlog.stdlib import get_logger

log = get_logger()


class DestinationDisplayValidator:
    """
    Validate DestinationDisplay
    """

    def __init__(self, journey_pattern):

        self.namespaces = {"x": journey_pattern.nsmap.get(None)}
        self.journey_pattern: _Element = journey_pattern
        self.journey_pattern_ref = self.journey_pattern.get("id")

    @property
    def vehicle_journeys(self) -> list[_Element]:
        """
        Get all VehicleJourney elements that reference this journey pattern.
        """
        root = self.journey_pattern.getroottree()
        xpath = (
            "//x:VehicleJourney[contains(x:JourneyPatternRef, "
            f"'{self.journey_pattern_ref}')]"
        )
        return root.xpath(xpath, namespaces=self.namespaces)

    @property
    def journey_pattern_sections(self) -> list[_Element]:
        """
        Get all JourneyPatternSection elements referenced by this journey pattern.
        """
        xpath = "x:JourneyPatternSectionRefs/text()"
        refs = self.journey_pattern.xpath(xpath, namespaces=self.namespaces)
        xpaths = [f"//x:JourneyPatternSection[@id='{ref}']" for ref in refs]

        sections: list[_Element] = []
        for xpath in xpaths:
            sections += self.journey_pattern.xpath(xpath, namespaces=self.namespaces)
        return sections

    def journey_pattern_has_display(self) -> bool:
        """
        Checks if the journey pattern has a DestinationDisplay as a direct child
        """
        displays = self.journey_pattern.xpath(
            "x:DestinationDisplay", namespaces=self.namespaces
        )
        return len(displays) > 0

    def links_have_dynamic_displays(self) -> bool:
        """
        Checks if all the timing links in the JourneyPatternSections
        Have DynamicDestinationDisplay at both their "From" and "To" points
        """
        for section in self.journey_pattern_sections:
            links = section.xpath(
                "x:JourneyPatternTimingLink", namespaces=self.namespaces
            )
            for link in links:
                from_display = link.xpath(
                    "x:From/x:DynamicDestinationDisplay", namespaces=self.namespaces
                )
                to_display = link.xpath(
                    "x:To/x:DynamicDestinationDisplay", namespaces=self.namespaces
                )
                if not all([to_display, from_display]):
                    return False
        return True

    def vehicle_journeys_have_displays(self) -> bool:
        """
        Checks all VehicleJourneys for this JourneyPatternSection
        To ensure they have DestinationDisplay
        """
        xpath = "x:DestinationDisplay"
        for journey in self.vehicle_journeys:
            display = journey.xpath(xpath, namespaces=self.namespaces)
            if not display:
                return False

        return True

    def validate(self):
        """
        True if ANY of these conditions are met in this order
           - The journey pattern has a destination display
           - All links have dynamic destination displays
           - All vehicle journeys have destination displays
        """
        if self.journey_pattern_has_display():
            return True

        if self.links_have_dynamic_displays():
            return True

        if self.vehicle_journeys_have_displays():
            return True

        return False


def has_destination_display(_context, patterns) -> bool:
    """
    First check if DestinationDisplay in JourneyPattern is provided.

    If not, we need to check in if DynamicDestinationDisplay is provided for
    each stop inside a JourneyPatternTimingLink.

    If both conditions above fail, then DestinationDisplay should
    mandatory nside VehicleJourney.
    """
    log.info(
        "Validation Start: Has Destination Display",
    )
    pattern = patterns[0]
    validator = DestinationDisplayValidator(pattern)
    return validator.validate()
