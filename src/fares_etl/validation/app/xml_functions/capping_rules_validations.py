from lxml.etree import _Element  # type: ignore

from ..constants import (
    NAMESPACE,
    TYPE_OF_FRAME_METADATA_SUBSTRING,
    TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING,
    ErrorMessages,
)
from .helpers import create_violation_response, extract_attribute


def validate_cappeddiscountright_rules(_context: None, composite_frames: _Element):
    """
    Check if mandatory capping rules element are present
    """
    for composite_frame in composite_frames:
        try:
            composite_frame_id = extract_attribute(composite_frames, "id")
        except KeyError:
            sourceline = composite_frame.sourceline
            return create_violation_response(
                sourceline, ErrorMessages.MESSAGE_OBSERVATION_COMPOSITE_FRAME_ID_MISSING
            )

        if TYPE_OF_FRAME_METADATA_SUBSTRING in composite_frame_id:
            continue

        fareframes_xpath = "x:frames/x:FareFrame"
        fareframes = composite_frame.xpath(fareframes_xpath, namespaces=NAMESPACE)

        for fareframe in fareframes:
            type_of_frame_refs = fareframe.xpath(
                "x:TypeOfFrameRef", namespaces=NAMESPACE
            )

            if not type_of_frame_refs:
                continue

            try:
                type_of_frame_ref_ref = extract_attribute(type_of_frame_refs, "ref")
            except KeyError:
                return ""

            if (
                not type_of_frame_ref_ref
                or TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in type_of_frame_ref_ref
            ):
                continue

            capped_discount_right_xpath = "x:fareProducts/x:CappedDiscountRight"
            capped_discount_right = fareframe.xpath(
                capped_discount_right_xpath, namespaces=NAMESPACE
            )

            if not capped_discount_right:
                continue

            capped_discount_right = capped_discount_right[0]

            if "id" not in capped_discount_right.attrib:
                sourceline = composite_frame.sourceline
                return create_violation_response(
                    sourceline,
                    ErrorMessages.MESSAGE_OBSERVATION_MISSING_CAPPED_DISCOUNT_RIGHT_ID,
                )

            capping_rule = capped_discount_right.xpath(
                "x:cappingRules/x:CappingRule", namespaces=NAMESPACE
            )[0]
            capping_rule_name = capping_rule.xpath(
                "string(x:Name)", namespaces=NAMESPACE
            )

            if not capping_rule_name:
                sourceline = capped_discount_right.sourceline
                return create_violation_response(
                    sourceline,
                    ErrorMessages.MESSAGE_OBSERVATION_MISSING_CAPPING_RULE_NAME,
                )

            capping_rule_period = capping_rule.xpath(
                "string(x:CappingPeriod)", namespaces=NAMESPACE
            )

            if not capping_rule_period or len(capping_rule_period) == 0:
                sourceline = capped_discount_right.sourceline
                return create_violation_response(
                    sourceline,
                    ErrorMessages.MESSAGE_OBSERVATION_MISSING_CAPPING_PERIOD,
                )

            capping_rule_validelelement_ref = capping_rule.xpath(
                "x:ValidableElementRef", namespaces=NAMESPACE
            )

            if not capping_rule_validelelement_ref:
                sourceline = capped_discount_right.sourceline
                return create_violation_response(
                    sourceline,
                    ErrorMessages.MESSAGE_OBSERVATION_MISSING_VALIDABLE_ELEMENT_REF,
                )

    return ""
