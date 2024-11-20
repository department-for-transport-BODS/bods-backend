import json
from typing import IO, Any, Callable

from pti.models import Schema
from pti.validators.functions import (
    cast_to_bool,
    cast_to_date,
    check_description_for_inbound_description,
    check_description_for_outbound_description,
    check_flexible_service_times,
    check_flexible_service_timing_status,
    check_inbound_outbound_description,
    check_service_group_validations,
    check_vehicle_journey_timing_links,
    contains_date,
    has_destination_display,
    has_flexible_or_standard_service,
    has_flexible_service_classification,
    has_name,
    has_prohibited_chars,
    has_servicedorganisation_working_days,
    is_member_of,
    regex,
    strip,
    to_days,
    today,
    validate_bank_holidays,
    validate_licence_number,
    validate_line_id,
    validate_lines,
    validate_modification_date_time,
    validate_non_naptan_stop_points,
    validate_run_time,
    validate_timing_link_stops,
)


class PTIValidator:
    def __init__(self, source: IO[Any]):
        json_ = json.load(source)
        self.schema = Schema(**json_)
        self.namespaces = self.schema.header.namespaces
        self.violations = []

        self.register_function("bool", cast_to_bool)
        self.register_function("contains_date", contains_date)
        self.register_function("check_flexible_service_timing_status", check_flexible_service_timing_status)

        # TODO: Requires DB interaction
        # self.register_function(
        #     "check_flexible_service_stop_point_ref",
        #     check_flexible_service_stop_point_ref,
        # )

        self.register_function(
            "check_inbound_outbound_description",
            check_inbound_outbound_description,
        )
        self.register_function(
            "check_description_for_inbound_description",
            check_description_for_inbound_description,
        )
        self.register_function(
            "check_description_for_outbound_description",
            check_description_for_outbound_description,
        )
        self.register_function("date", cast_to_date)
        self.register_function("days", to_days)
        self.register_function("has_destination_display", has_destination_display)
        self.register_function("has_name", has_name)
        self.register_function(
            "has_flexible_or_standard_service", has_flexible_or_standard_service
        )
        self.register_function(
            "has_flexible_service_classification", has_flexible_service_classification
        )
        self.register_function("has_prohibited_chars", has_prohibited_chars)
        self.register_function(
            "check_service_group_validations", check_service_group_validations
        )
        self.register_function(
            "check_flexible_service_times",
            check_flexible_service_times,
        )
        self.register_function("in", is_member_of)
        self.register_function("regex", regex)
        self.register_function("strip", strip)
        self.register_function("today", today)
        self.register_function("validate_line_id", validate_line_id)
        self.register_function("validate_lines", validate_lines)
        self.register_function(
            "validate_modification_date_time", validate_modification_date_time
        )
        self.register_function(
            "validate_non_naptan_stop_points", validate_non_naptan_stop_points
        )
        self.register_function("validate_run_time", validate_run_time)
        self.register_function("validate_timing_link_stops", validate_timing_link_stops)
        self.register_function("validate_bank_holidays", validate_bank_holidays)

        # TODO: Requires DB interaction
        # self.register_function("validate_service_code", validate_service_codes)

        self.register_function(
            "check_vehicle_journey_timing_links", check_vehicle_journey_timing_links
        )
        self.register_function("validate_licence_number", validate_licence_number)

        self.register_function(
            "has_servicedorganisation_working_days",
            has_servicedorganisation_working_days,
        )
        


    def register_function(self, key: str, function: Callable) -> None:
        self.fns[key] = function

    def is_valid(self, source: IO[Any]) -> bool:
        raise NotImplementedError()
