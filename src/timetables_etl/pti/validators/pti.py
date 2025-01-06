import json
import logging
from pathlib import Path
from typing import IO, Any, Callable
from urllib.parse import unquote

from common_layer.database.client import SqlDB
from common_layer.dynamodb.client import DynamoDB
from common_layer.pti.models import Observation, Schema, Violation
from lxml import etree

from ..constants import FLEXIBLE_SERVICE, STANDARD_SERVICE
from .functions import (
    cast_to_bool,
    cast_to_date,
    check_description_for_inbound_description,
    check_description_for_outbound_description,
    check_flexible_service_times,
    check_flexible_service_timing_status,
    check_inbound_outbound_description,
    check_service_group_validations,
    contains_date,
    get_flexible_service_stop_point_ref_validator,
    get_lines_validator,
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
    validate_licence_number,
    validate_line_id,
    validate_modification_date_time,
    validate_non_naptan_stop_points,
    validate_run_time,
    validate_timing_link_stops,
)
from .holidays import get_validate_bank_holidays

logger = logging.getLogger(__name__)


class PTIValidator:
    def __init__(self, source: IO[Any], dynamo: DynamoDB, db: SqlDB):
        json_ = json.load(source)
        self.schema = Schema(**json_)
        self.namespaces = self.schema.header.namespaces
        self.violations = []

        self.fns = etree.FunctionNamespace(None)
        self.register_function("bool", cast_to_bool)
        self.register_function("contains_date", contains_date)
        self.register_function(
            "check_flexible_service_timing_status", check_flexible_service_timing_status
        )

        self.register_function(
            "check_flexible_service_stop_point_ref",
            get_flexible_service_stop_point_ref_validator(db),
        )

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
        self.register_function("validate_lines", get_lines_validator(db))

        self.register_function(
            "validate_modification_date_time", validate_modification_date_time
        )
        self.register_function(
            "validate_non_naptan_stop_points", validate_non_naptan_stop_points
        )
        self.register_function("validate_run_time", validate_run_time)
        self.register_function("validate_timing_link_stops", validate_timing_link_stops)

        self.register_function(
            "validate_bank_holidays", get_validate_bank_holidays(dynamo, db)
        )

        self.register_function("validate_licence_number", validate_licence_number)

        self.register_function(
            "has_servicedorganisation_working_days",
            has_servicedorganisation_working_days,
        )

    def register_function(self, key: str, function: Callable) -> None:
        self.fns[key] = function

    def add_violation(self, violation: Violation) -> None:
        self.violations.append(violation)

    def check_observation(
        self, observation: Observation, element: etree._Element
    ) -> None:
        for rule in observation.rules:
            result = element.xpath(rule.test, namespaces=self.namespaces)
            if not result:
                name = element.xpath("local-name(.)", namespaces=self.namespaces)
                violation = Violation(
                    line=element.sourceline,
                    name=name,
                    filename=unquote(Path(element.base).name),
                    observation=observation,
                    element_text=element.text,
                )
                self.add_violation(violation)
                break

    def check_service_type(self, document):
        servie_classification_xpath = (
            "//x:Services/x:Service/x:ServiceClassification/x:Flexible"
        )
        service_classification = document.xpath(
            servie_classification_xpath, namespaces=self.namespaces
        )

        flexible_service_xpath = "//x:Services/x:Service/x:FlexibleService"
        flexible_service = document.xpath(
            flexible_service_xpath, namespaces=self.namespaces
        )

        if service_classification or flexible_service:
            return FLEXIBLE_SERVICE
        return STANDARD_SERVICE

    def is_valid(self, source: IO[Any]) -> bool:
        document = etree.parse(source)
        txc_service_type = self.check_service_type(document)

        service_observations = []
        service_observations = [
            x
            for x in self.schema.observations
            if x.service_type == txc_service_type or x.service_type == "All"
        ]
        logger.info(f"Checking observations for XML file")
        for observation in service_observations:
            elements = document.xpath(observation.context, namespaces=self.namespaces)
            for element in elements:
                self.check_observation(observation, element)
        logger.info(f"Completed observations for the XML file")
        return len(self.violations) == 0
