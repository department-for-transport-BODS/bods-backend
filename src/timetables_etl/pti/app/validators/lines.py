"""
Validations related to Lines
"""

import itertools
from collections import defaultdict
from typing import Any, Callable

from attr import dataclass
from common_layer.dynamodb.client import NaptanStopPointDynamoDBClient
from common_layer.xml.txc.models import AnnotatedStopPointRef, TXCData, TXCStopPoint
from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ..constants import NAMESPACE
from .base import BaseValidator

log = get_logger()


@dataclass
class StopInfo:
    """
    Model containing the StopInfo required for PTI line validation
    """

    stop_areas: list[str] = []
    locality_name: str | None = None


class LinesValidator(BaseValidator):
    """
    Class for running Line validations
    """

    def __init__(self, *args: Any, stop_info_map: dict[str, StopInfo], **kwargs: Any):
        self._stop_info_map = stop_info_map
        super().__init__(*args, **kwargs)

    def _flatten_stop_areas(self, stops: list[str]) -> set[str]:
        """
        Given list of stops, returns flattened set of stop areas
        """
        stop_areas: list[str] = []
        for stop in stops:
            stop_info = self._stop_info_map.get(stop, None)
            stop_areas += stop_info.stop_areas if stop_info else []
        return set(stop_areas)

    def check_for_common_journey_patterns(self) -> bool:
        """
        Check whether related lines share a JourneyPattern with the
        designated main line.
        """
        line_to_journey_pattern: dict[str, list[str]] = {}
        for line in self.lines:
            jp_refs = self.get_journey_pattern_refs_by_line_ref(line.ref)
            line_to_journey_pattern[line.ref] = jp_refs

        combinations = itertools.combinations(line_to_journey_pattern.keys(), 2)
        for line1, line2 in combinations:
            line1_refs = line_to_journey_pattern.get(line1)
            line2_refs = line_to_journey_pattern.get(line2)

            if set(line1_refs).isdisjoint(line2_refs):  # pyright: ignore
                return False
        return True

    def get_locality_name_from_annotated_stop_point_ref(self, ref: str) -> str | None:
        """
        Get the LocalityName of an AnnotatedStopPointRef from its StopPointRef.
        """
        stop_info = self._stop_info_map.get(ref)
        if stop_info and stop_info.locality_name:
            return stop_info.locality_name
        return None

    def check_for_common_stops_points(self) -> bool:
        # pylint: disable=too-many-locals
        """
        Check if all lines share common stop points.
        """
        line_to_stops: dict[str, list[str]] = defaultdict(list)
        for line in self.lines:
            jp_refs = self.get_journey_pattern_refs_by_line_ref(line.ref)
            for jp_ref in jp_refs:
                stops = self.get_stop_point_ref_from_journey_pattern_ref(jp_ref)
                line_to_stops[line.ref] += stops

        combinations = itertools.combinations(line_to_stops.keys(), 2)
        for line1, line2 in combinations:
            line1_stops = line_to_stops.get(line1, [])
            line2_stops = line_to_stops.get(line2, [])
            line1_stop_areas = self._flatten_stop_areas(line1_stops)
            line2_stop_areas = self._flatten_stop_areas(line2_stops)

            disjointed_stop_areas = line1_stop_areas.isdisjoint(line2_stop_areas)
            disjointed_stops = set(line1_stops).isdisjoint(line2_stops)

            line1_localities = [
                self.get_locality_name_from_annotated_stop_point_ref(ref)
                for ref in line1_stops
            ]
            line1_localities = [name for name in line1_localities if name]
            line2_localities = [
                self.get_locality_name_from_annotated_stop_point_ref(ref)
                for ref in line2_stops
            ]
            line2_localities = [name for name in line2_localities if name]
            disjointed_localities = set(line1_localities).isdisjoint(line2_localities)

            if all([disjointed_stop_areas, disjointed_stops, disjointed_localities]):
                return False

        return True

    def validate(self) -> bool:
        """
        Validates that all Line that appears in Lines are related.

        """
        if len(self.lines) < 2:
            return True

        if self.check_for_common_journey_patterns():
            return True

        if self.check_for_common_stops_points():
            return True

        return False


def get_stop_info_map(
    naptan_client: NaptanStopPointDynamoDBClient, txc_data: TXCData
) -> dict[str, StopInfo]:
    """
    Build a map between atco codes and StopInfo required for line validation

    Returns:
        Dict of {AtcoCode: StopInfo}
    """
    atco_codes = [
        (
            stop_point.AtcoCode
            if isinstance(stop_point, TXCStopPoint)
            else stop_point.StopPointRef
        )
        for stop_point in txc_data.StopPoints
    ]
    stop_points, _ = naptan_client.get_by_atco_codes(atco_codes)

    # Populate map with StopAreas for all stops fetched from Naptan
    stop_info_map: dict[str, StopInfo] = {
        stop_point.AtcoCode: StopInfo(stop_areas=stop_point.StopAreas or [])
        for stop_point in stop_points
    }

    # Populate map with LocalityName for AnnotetedStopPointRefs
    for stop in txc_data.StopPoints:
        if isinstance(stop, AnnotatedStopPointRef):
            stop_ref = stop.StopPointRef
            if stop_ref in stop_info_map:
                stop_info_map[stop_ref].locality_name = stop.LocalityName
            else:
                stop_info_map[stop_ref] = StopInfo(locality_name=stop.LocalityName)

    return stop_info_map


def get_lines_validator(
    naptan_client: NaptanStopPointDynamoDBClient, txc_data: TXCData
) -> Callable[..., bool]:
    """
    Creates and returns a validator function for NAPTAN lines XML elements.
    """
    stop_info_map = get_stop_info_map(naptan_client, txc_data)

    def validate_lines(_: _Element | None, lines_list: list[_Element]) -> bool:
        """
        Validates NAPTAN lines XML elements against stop area data.
        """
        log.info(
            "Validation Start: Lines",
            lines_count=len(lines_list),
        )
        lines = lines_list[0]
        validator = LinesValidator(lines, stop_info_map=stop_info_map)
        return validator.validate()

    return validate_lines


def validate_line_id(_: _Element | None, lines: list[_Element]) -> bool:
    """
    Validates that Line@id has the correct format.
    """
    log.info(
        "Validation Start: Line ID",
        count=len(lines),
    )
    line = lines[0]

    xpath = "string(@id)"
    line_id = line.xpath(xpath, namespaces=NAMESPACE)

    xpath = "string(//x:Operators/x:Operator/x:NationalOperatorCode)"
    noc = line.xpath(xpath, namespaces=NAMESPACE)

    xpath = "string(../../x:ServiceCode)"
    service_code = line.xpath(xpath, namespaces=NAMESPACE)

    xpath = "string(x:LineName)"
    line_name = line.xpath(xpath, namespaces=NAMESPACE)
    line_name = line_name.replace(" ", "")

    expected_line_id = f"{noc}:{service_code}:{line_name}"
    return line_id.startswith(expected_line_id)
