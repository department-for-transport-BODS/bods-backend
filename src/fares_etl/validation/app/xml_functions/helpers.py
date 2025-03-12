"""
XML Helper Functions
"""

from lxml.etree import _Element  # type: ignore

from ..types import XMLViolationDetail


def extract_text(
    elements: list[_Element] | list[str] | _Element | str, default: str = ""
) -> str:
    """
    Extract text from element
    """
    if isinstance(elements, list) and len(elements) > 0:
        item = elements[0]
        if isinstance(item, str):
            text = item
        else:
            text = item.text
    elif isinstance(elements, str):
        text = elements
    elif isinstance(elements, _Element) and hasattr(elements, "text"):
        text = elements.text
    else:
        text = default
    return text or ""


def extract_attribute(
    elements: list[_Element] | _Element, attribute_name: str, default: str = ""
) -> str:
    """
    Extract attribute from element
    """
    if isinstance(elements, list) and len(elements) > 0:
        item = elements[0]
        try:
            element_attribute = item.attrib[attribute_name]
        except KeyError:
            element_attribute = ""
            raise

    elif isinstance(elements, _Element):
        try:
            element_attribute = elements.attrib[attribute_name]
        except KeyError:
            element_attribute = ""
            raise
    else:
        element_attribute = default
    return element_attribute


def create_violation_response(sourceline: str | int | None, message: str):
    """
    Create violation response
    """
    response_details = XMLViolationDetail(sourceline, message)
    return response_details.__list__()


def find_indices(ref_list: list[str], ref: str):
    """
    Find all indices of a given reference string in a list of strings.
    """
    return {index for index, ref_value in enumerate(ref_list) if ref_value == ref}
