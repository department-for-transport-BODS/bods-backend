"""
FrameDefaults
"""

from lxml.etree import _Element  # type: ignore

from ....utils import parse_xml_attribute
from ...models.data_objects.netex_frame_composite import CodespaceRef
from ...models.fare_frame.netex_frame_defaults import (
    DefaultLocaleStructure,
    FrameDefaultsStructure,
)
from ..netex_utility import get_netex_element, get_netex_text, parse_versioned_ref


def parse_default_locale(elem: _Element) -> DefaultLocaleStructure:
    """Parse DefaultLocale element"""
    return DefaultLocaleStructure(
        TimeZoneOffset=get_netex_text(elem, "TimeZoneOffset"),
        TimeZone=get_netex_text(elem, "TimeZone"),
        SummerTimeZoneOffset=get_netex_text(elem, "SummerTimeZoneOffset"),
        SummerTimeZone=get_netex_text(elem, "SummerTimeZone"),
        DefaultLanguage=get_netex_text(elem, "DefaultLanguage"),
    )


def parse_frame_defaults(elem: _Element) -> FrameDefaultsStructure:
    """Parse Frame Defaults"""
    codespace_ref = None
    default_codespace = get_netex_element(elem, "DefaultCodespaceRef")
    if default_codespace is not None:
        codespace_ref_data = parse_xml_attribute(default_codespace, "ref")
        if codespace_ref_data:
            codespace_ref = CodespaceRef(ref=codespace_ref_data)

    default_locale = None
    default_locale_elem = get_netex_element(elem, "DefaultLocale")
    if default_locale_elem is not None:
        default_locale = parse_default_locale(default_locale_elem)

    return FrameDefaultsStructure(
        DefaultCodespaceRef=codespace_ref,
        DefaultDataSourceRef=parse_versioned_ref(elem, "DefaultDataSourceRef"),
        DefaultResponsibilitySetRef=parse_versioned_ref(
            elem, "DefaultResponsibilitySetRef"
        ),
        DefaultLocale=default_locale,
        DefaultLocationSystem=get_netex_text(elem, "DefaultLocationSystem"),
        DefaultSystemOfUnits=get_netex_text(elem, "DefaultSystemOfUnits"),
        DefaultCurrency=get_netex_text(elem, "DefaultCurrency"),
    )
