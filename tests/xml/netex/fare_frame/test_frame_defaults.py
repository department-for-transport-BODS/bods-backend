"""
Test Parsing Frame Defaults
"""

import pytest
from common_layer.xml.netex.models.data_objects.netex_codespaces import CodespaceRef
from common_layer.xml.netex.models.fare_frame.netex_frame_defaults import (
    DefaultLocaleStructure,
    FrameDefaultsStructure,
)
from common_layer.xml.netex.models.netex_utility import VersionedRef
from common_layer.xml.netex.parser.data_objects.netex_frame_defaults import (
    parse_default_locale,
    parse_frame_defaults,
)

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import parse_xml_str_as_netex


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <DefaultLocale>
                <TimeZoneOffset>0</TimeZoneOffset>
                <TimeZone>GMT</TimeZone>
                <SummerTimeZoneOffset>+1</SummerTimeZoneOffset>
                <SummerTimeZone>BST</SummerTimeZone>
                <DefaultLanguage>en</DefaultLanguage>
            </DefaultLocale>
            """,
            DefaultLocaleStructure(
                TimeZoneOffset="0",
                TimeZone="GMT",
                SummerTimeZoneOffset="+1",
                SummerTimeZone="BST",
                DefaultLanguage="en",
            ),
            id="Full default locale",
        ),
        pytest.param(
            """
            <DefaultLocale>
                <TimeZone>GMT</TimeZone>
                <DefaultLanguage>en</DefaultLanguage>
            </DefaultLocale>
            """,
            DefaultLocaleStructure(
                TimeZone="GMT",
                DefaultLanguage="en",
            ),
            id="Partial default locale",
        ),
    ],
)
def test_parse_default_locale(xml_str: str, expected: DefaultLocaleStructure) -> None:
    """Test parsing of default locale with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_default_locale(elem)
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <FrameDefaults>
                <DefaultCodespaceRef ref="fxc"></DefaultCodespaceRef>
                <DefaultDataSourceRef ref="fxc:common" version="fxc:v1.0"></DefaultDataSourceRef>
                <DefaultResponsibilitySetRef ref="fxc:FXC_metadata" version="fxc:v1.0"></DefaultResponsibilitySetRef>
                <DefaultLocale>
                    <TimeZoneOffset>0</TimeZoneOffset>
                    <TimeZone>GMT</TimeZone>
                    <SummerTimeZoneOffset>+1</SummerTimeZoneOffset>
                    <SummerTimeZone>BST</SummerTimeZone>
                    <DefaultLanguage>en</DefaultLanguage>
                </DefaultLocale>
                <DefaultLocationSystem>WGS84</DefaultLocationSystem>
                <DefaultSystemOfUnits>SiKilometresAndMetres</DefaultSystemOfUnits>
                <DefaultCurrency>GBP</DefaultCurrency>
            </FrameDefaults>
            """,
            FrameDefaultsStructure(
                DefaultCodespaceRef=CodespaceRef(ref="fxc"),
                DefaultDataSourceRef=VersionedRef(
                    ref="fxc:common",
                    version="fxc:v1.0",
                ),
                DefaultResponsibilitySetRef=VersionedRef(
                    ref="fxc:FXC_metadata",
                    version="fxc:v1.0",
                ),
                DefaultLocale=DefaultLocaleStructure(
                    TimeZoneOffset="0",
                    TimeZone="GMT",
                    SummerTimeZoneOffset="+1",
                    SummerTimeZone="BST",
                    DefaultLanguage="en",
                ),
                DefaultLocationSystem="WGS84",
                DefaultSystemOfUnits="SiKilometresAndMetres",
                DefaultCurrency="GBP",
            ),
            id="Full frame defaults",
        ),
        pytest.param(
            """
            <FrameDefaults>
                <DefaultCodespaceRef ref="fxc"></DefaultCodespaceRef>
                <DefaultCurrency>GBP</DefaultCurrency>
            </FrameDefaults>
            """,
            FrameDefaultsStructure(
                DefaultCodespaceRef=CodespaceRef(ref="fxc"),
                DefaultCurrency="GBP",
            ),
            id="Minimal frame defaults",
        ),
    ],
)
def test_parse_frame_defaults(xml_str: str, expected: FrameDefaultsStructure) -> None:
    """Test parsing of frame defaults with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_frame_defaults(elem)
    assert_model_equal(result, expected)


def test_parse_frame_defaults_empty_codespace() -> None:
    """Test parsing of frame defaults with empty codespace ref."""
    xml_str = """
        <FrameDefaults>
            <DefaultCodespaceRef></DefaultCodespaceRef>
        </FrameDefaults>
        """
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_frame_defaults(elem)
    assert result.DefaultCodespaceRef is None
