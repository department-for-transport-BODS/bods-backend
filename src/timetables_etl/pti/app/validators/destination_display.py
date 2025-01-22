from lxml.etree import _Element


class DestinationDisplayValidator:
    def __init__(self, journey_pattern: _Element):

        self.namespaces = {"x": journey_pattern.nsmap.get(None)}
        self.journey_pattern = journey_pattern
        self.journey_pattern_ref = self.journey_pattern.get("id")

    @property
    def vehicle_journeys(self):
        root = self.journey_pattern.getroottree()
        xpath = (
            "//x:VehicleJourney[contains(x:JourneyPatternRef, "
            f"'{self.journey_pattern_ref}')]"
        )
        return root.xpath(xpath, namespaces=self.namespaces)

    @property
    def journey_pattern_sections(self):
        xpath = "x:JourneyPatternSectionRefs/text()"
        refs = self.journey_pattern.xpath(xpath, namespaces=self.namespaces)
        xpaths = [f"//x:JourneyPatternSection[@id='{ref}']" for ref in refs]

        sections = []
        for xpath in xpaths:
            sections += self.journey_pattern.xpath(xpath, namespaces=self.namespaces)
        return sections

    def journey_pattern_has_display(self):
        displays = self.journey_pattern.xpath(
            "x:DestinationDisplay", namespaces=self.namespaces
        )
        return len(displays) > 0

    def links_have_dynamic_displays(self):
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

    def vehicle_journeys_have_displays(self):
        xpath = "x:DestinationDisplay"
        for journey in self.vehicle_journeys:
            display = journey.xpath(xpath, namespaces=self.namespaces)
            if not display:
                return False

        return True

    def validate(self):
        if self.journey_pattern_has_display():
            return True

        if self.links_have_dynamic_displays():
            return True

        if self.vehicle_journeys_have_displays():
            return True

        return False
