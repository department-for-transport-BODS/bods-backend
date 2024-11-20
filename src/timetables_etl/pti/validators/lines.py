import itertools
from pti.validators.base import BaseValidator


# TODO: No tests found for this class
class LinesValidator(BaseValidator):
    def __init__(self, *args, stop_area_map=None, **kwargs):
        self._stop_area_map = stop_area_map or {}
        super().__init__(*args, **kwargs)

    def _flatten_stop_areas(self, stops: list[str]) -> set[str]:
        stop_areas = []
        for stop in stops:
            stop_areas += self._stop_area_map.get(stop, [])
        return set(stop_areas)

    def check_for_common_journey_patterns(self) -> bool:
        """
        Check whether related lines share a JourneyPattern with the
        designated main line.
        """
        line_to_journey_pattern = {}
        for line in self.lines:
            jp_refs = self.get_journey_pattern_refs_by_line_ref(line.ref)
            line_to_journey_pattern[line.ref] = jp_refs

        combinations = itertools.combinations(line_to_journey_pattern.keys(), 2)
        for line1, line2 in combinations:
            line1_refs = line_to_journey_pattern.get(line1)
            line2_refs = line_to_journey_pattern.get(line2)

            if set(line1_refs).isdisjoint(line2_refs):
                return False
        return True
