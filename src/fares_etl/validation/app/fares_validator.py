"""
Fares Validator
"""

import os
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote

from common_layer.dynamodb.models import FaresViolation
from lxml import etree
from lxml.etree import _Element  # type: ignore

from .types import Observation, Schema, XMLFile
from .xml_functions.capping_rules_validations import validate_cappeddiscountright_rules
from .xml_functions.composite_frame import (
    check_composite_frame_valid_between,
    check_resource_frame_operator_name,
    check_resource_frame_organisation_elements,
    check_type_of_frame_ref_ref,
    check_value_of_type_of_frame_ref,
)
from .xml_functions.fare_frame_fare_structure_elements import (
    all_fare_structure_element_checks,
    check_fare_structure_element,
    check_frequency_of_use,
    check_generic_parameters_for_access,
    check_generic_parameters_for_eligibility,
    check_type_of_fare_structure_element_ref,
    check_validity_grouping_type_for_access,
    check_validity_parameter_for_access,
)
from .xml_functions.fare_tables import is_uk_pi_fare_price_frame_present
from .xml_functions.fare_zones import (
    is_fare_zones_present_in_fare_frame,
    is_name_present_in_fare_frame,
)
from .xml_functions.mandatory_fareframe_fare_products import (
    check_access_right_elements,
    check_fare_product_validable_elements,
    check_fare_products,
    check_fare_products_charging_type,
    check_fare_products_type_ref,
    check_product_type,
)
from .xml_functions.mandatory_fareframe_tariffs import (
    check_tariff_basis,
    check_tariff_operator_ref,
    check_tariff_validity_conditions,
    check_type_of_tariff_ref_values,
)
from .xml_functions.mandatory_type_of_frame_refs import (
    check_fare_frame_type_of_frame_ref_present_fare_price,
    check_fare_frame_type_of_frame_ref_present_fare_product,
    check_resource_frame_type_of_frame_ref_present,
)
from .xml_functions.product_type_checks import (
    is_fare_structure_element_present,
    is_generic_parameter_limitations_present,
    is_individual_time_interval_present_in_tariffs,
    is_time_interval_name_present_in_tariffs,
    is_time_intervals_present_in_tarrifs,
)
from .xml_functions.sales_offer_packages import (
    check_dist_assignments,
    check_fare_product_ref,
    check_payment_methods,
    check_sale_offer_package_elements,
    check_sales_offer_package,
)
from .xml_functions.service_frame import (
    check_lines_operator_ref_present,
    check_lines_public_code_present,
    is_lines_present_in_service_frame,
    is_schedule_stop_points,
    is_service_frame_present,
)


class FaresValidator:
    """
    Validate NeTEx file against a json schema.
    """

    def __init__(self):
        self.schema = Schema.from_path(
            Path(f"{os.path.dirname(os.path.realpath(__file__))}/schema/schema.json")
        )
        self.namespaces = self.schema.header.namespaces
        self.violations: list[FaresViolation] = []

        self.fns = etree.FunctionNamespace(None)
        self.register_function(
            "is_time_intervals_present_in_tarrifs", is_time_intervals_present_in_tarrifs
        )
        self.register_function(
            "is_individual_time_interval_present_in_tariffs",
            is_individual_time_interval_present_in_tariffs,
        )
        self.register_function(
            "is_time_interval_name_present_in_tariffs",
            is_time_interval_name_present_in_tariffs,
        )
        self.register_function(
            "is_fare_structure_element_present", is_fare_structure_element_present
        )
        self.register_function(
            "is_generic_parameter_limitations_present",
            is_generic_parameter_limitations_present,
        )
        self.register_function(
            "is_fare_zones_present_in_fare_frame", is_fare_zones_present_in_fare_frame
        )
        self.register_function(
            "check_value_of_type_of_frame_ref", check_value_of_type_of_frame_ref
        )
        self.register_function("is_service_frame_present", is_service_frame_present)
        self.register_function(
            "is_lines_present_in_service_frame", is_lines_present_in_service_frame
        )
        self.register_function("is_schedule_stop_points", is_schedule_stop_points)
        self.register_function(
            "check_lines_public_code_present", check_lines_public_code_present
        )
        self.register_function(
            "check_lines_operator_ref_present", check_lines_operator_ref_present
        )
        self.register_function(
            "all_fare_structure_element_checks", all_fare_structure_element_checks
        )
        self.register_function(
            "check_fare_structure_element", check_fare_structure_element
        )
        self.register_function(
            "check_type_of_fare_structure_element_ref",
            check_type_of_fare_structure_element_ref,
        )
        self.register_function(
            "check_type_of_frame_ref_ref", check_type_of_frame_ref_ref
        )
        self.register_function(
            "check_type_of_tariff_ref_values", check_type_of_tariff_ref_values
        )
        self.register_function("check_tariff_operator_ref", check_tariff_operator_ref)
        self.register_function("check_tariff_basis", check_tariff_basis)
        self.register_function(
            "check_tariff_validity_conditions", check_tariff_validity_conditions
        )
        self.register_function(
            "check_fare_frame_type_of_frame_ref_present_fare_price",
            check_fare_frame_type_of_frame_ref_present_fare_price,
        )
        self.register_function(
            "check_fare_frame_type_of_frame_ref_present_fare_product",
            check_fare_frame_type_of_frame_ref_present_fare_product,
        )
        self.register_function(
            "is_uk_pi_fare_price_frame_present", is_uk_pi_fare_price_frame_present
        )
        self.register_function("check_fare_products", check_fare_products)
        self.register_function(
            "check_fare_products_type_ref",
            check_fare_products_type_ref,
        )
        self.register_function(
            "check_fare_products_charging_type",
            check_fare_products_charging_type,
        )
        self.register_function(
            "check_fare_product_validable_elements",
            check_fare_product_validable_elements,
        )
        self.register_function(
            "check_access_right_elements", check_access_right_elements
        )
        self.register_function("check_sales_offer_package", check_sales_offer_package)
        self.register_function("check_product_type", check_product_type)
        self.register_function("check_dist_assignments", check_dist_assignments)
        self.register_function(
            "check_payment_methods",
            check_payment_methods,
        )
        self.register_function(
            "check_sale_offer_package_elements", check_sale_offer_package_elements
        )
        self.register_function("check_fare_product_ref", check_fare_product_ref)
        self.register_function(
            "check_generic_parameters_for_access", check_generic_parameters_for_access
        )
        self.register_function(
            "check_validity_grouping_type_for_access",
            check_validity_grouping_type_for_access,
        )
        self.register_function(
            "check_validity_parameter_for_access", check_validity_parameter_for_access
        )
        self.register_function(
            "check_generic_parameters_for_eligibility",
            check_generic_parameters_for_eligibility,
        )
        self.register_function(
            "check_frequency_of_use",
            check_frequency_of_use,
        )
        self.register_function(
            "is_name_present_in_fare_frame", is_name_present_in_fare_frame
        )
        self.register_function(
            "check_composite_frame_valid_between", check_composite_frame_valid_between
        )
        self.register_function(
            "check_resource_frame_type_of_frame_ref_present",
            check_resource_frame_type_of_frame_ref_present,
        )
        self.register_function(
            "check_resource_frame_organisation_elements",
            check_resource_frame_organisation_elements,
        )
        self.register_function(
            "check_resource_frame_operator_name", check_resource_frame_operator_name
        )
        self.register_function(
            "validate_cappeddiscountright_rules", validate_cappeddiscountright_rules
        )

    def register_function(
        self, key: str, function: Callable[[None, _Element], Any]
    ) -> None:
        """
        Registers a validation function to lxml
        """
        self.fns[key] = function

    def check_observation(self, observation: Observation, element: _Element) -> None:
        """
        Checks a given element against a certain observation
        """
        for rule in observation.rules:
            result = element.xpath(rule.test, namespaces=self.namespaces)
            if len(result):
                try:
                    line = int(result[0]) if result[0] else None
                except ValueError:
                    line = None

                violation = FaresViolation(
                    line=line,
                    filename=unquote(Path(element.base or "").name),
                    observation=result[1],
                    category=observation.category,
                )
                self.violations.append(violation)

    def get_violations(self, source: XMLFile[Any]) -> list[FaresViolation]:
        """
        Checks a given source file against the json schema
        """
        document = etree.parse(source)
        for observation in self.schema.observations:
            elements = document.xpath(observation.context, namespaces=self.namespaces)
            for element in elements:
                self.check_observation(observation, element)

        return self.violations
