"""
Pytest Helpers
"""

import pytest
from lxml import etree
from pydantic import BaseModel
from rich.pretty import pprint


def pretty_format_xml(data: str) -> str:
    """
    Make it easier to read the test output by pretty pretinging
    """

    root = etree.fromstring(data)
    pretty_xml = etree.tostring(root, pretty_print=True, encoding="unicode")
    return pretty_xml


def assert_model_equal(result: BaseModel, expected: BaseModel) -> None:
    """
    Compare the fields of Pydantic model individually as == fails
    """
    model_name = result.__class__.__name__
    for field in result.model_fields:
        result_value = getattr(result, field)
        expected_value = getattr(expected, field)
        try:
            assert result_value == expected_value
        except AssertionError as e:
            pprint(f"AssertionError {model_name} field {field} does not match:")
            pprint("Result")
            pprint(result_value)
            pprint("Expected:")
            pprint(expected_value)
            raise e


def compare_xml(result: etree._Element, expected: str):
    """
    Compare XML for Tests
    First converts to canonicalized form which standardises the output
    i.e. Removes new lines and converts <tag/> to <tag><tag>
    """
    result_canon = etree.canonicalize(result, strip_text=True)
    expected = etree.canonicalize(expected, strip_text=True)
    if result_canon != expected:
        with pytest.raises(AssertionError) as excinfo:
            expected_xml = pretty_format_xml(expected)
            actual_xml = pretty_format_xml(result_canon)
            assert False, f"\nExpected:\n{expected_xml}\n\nActual:\n{actual_xml}"
        pytest.fail(str(excinfo.value))
