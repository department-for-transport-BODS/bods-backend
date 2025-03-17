# pylint: disable=too-many-return-statements,duplicate-code

"""
Fare Tables
"""

from lxml.etree import _Element  # type: ignore

from ..constants import (
    NAMESPACE,
    TYPE_OF_FRAME_FARE_TABLES_REF_SUBSTRING,
    ErrorMessages,
)
from ..types import XMLViolationDetail
from .helpers import extract_attribute


def is_uk_pi_fare_price_frame_present(_context: None, fare_frames: _Element):
    """
    Check if mandatory fareTables elements missing for FareFrame - UK_PI_FARE_PRICE
    FareFrame UK_PI_FARE_PRICE is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)

    if not type_of_frame_refs:
        return ""

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_refs, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_FARE_TABLES_REF_SUBSTRING not in type_of_frame_ref_ref:
        return ""

    xpath = "x:fareTables"
    fare_tables = fare_frame.xpath(xpath, namespaces=NAMESPACE)

    if not fare_tables:
        sourceline_fare_frame = fare_frame.sourceline
        response_details = XMLViolationDetail(
            sourceline_fare_frame,
            ErrorMessages.MESSAGE_OBSERVATION_FARE_TABLES_MISSING,
        )
        response = response_details.__list__()
        return response

    xpath = "x:fareTables/x:FareTable"
    fare_table = fare_frame.xpath(xpath, namespaces=NAMESPACE)

    if not fare_table:
        sourceline_fare_tables = fare_tables[0].sourceline
        response_details = XMLViolationDetail(
            sourceline_fare_tables,
            ErrorMessages.MESSAGE_OBSERVATION_FARE_TABLE_MISSING,
        )
        response = response_details.__list__()
        return response

    xpath = "x:fareTables/x:FareTable/x:pricesFor"
    prices_for = fare_frame.xpath(xpath, namespaces=NAMESPACE)

    if not prices_for:
        sourceline_fare_table = fare_table[0].sourceline
        response_details = XMLViolationDetail(
            sourceline_fare_table,
            ErrorMessages.MESSAGE_OBSERVATION_PRICES_FOR_MISSING,
        )
        response = response_details.__list__()
        return response

    return ""
