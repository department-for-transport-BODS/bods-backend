"""
Test Helper Functions
"""

from datetime import UTC, datetime, timedelta, timezone

import pytest
from common_layer.xml.netex.models import MultilingualString, VersionedRef
from common_layer.xml.netex.parser import parse_timestamp
from common_layer.xml.netex.parser.netex_utility import (
    parse_multilingual_string,
    parse_versioned_ref,
)

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import (
    parse_xml_str_as_netex,
    parse_xml_str_as_netex_wrapped,
)


@pytest.mark.parametrize(
    "xml_str, element_name, expected_result",
    [
        pytest.param(
            """<Timestamp>2024-02-14T15:30:00Z</Timestamp>""",
            "Timestamp",
            datetime(2024, 2, 14, 15, 30, 0, tzinfo=UTC),
            id="Valid UTC timestamp",
        ),
        pytest.param(
            """<FromDate>2023-12-31T23:59:59Z</FromDate>""",
            "FromDate",
            datetime(2023, 12, 31, 23, 59, 59, tzinfo=UTC),
            id="Valid timestamp at year boundary",
        ),
        pytest.param(
            """<Timestamp></Timestamp>""",
            "Timestamp",
            None,
            id="Empty timestamp element",
        ),
        pytest.param(
            """<Timestamp />""",
            "Timestamp",
            None,
            id="Self-closing empty timestamp element",
        ),
        pytest.param(
            """<Timestamp>2024-02-14T15:30:00+00:00</Timestamp>""",
            "Timestamp",
            datetime(2024, 2, 14, 15, 30, 0, tzinfo=UTC),
            id="Valid ISO format with explicit UTC offset",
        ),
        pytest.param(
            """<Timestamp>2024-02-14T16:30:00+01:00</Timestamp>""",
            "Timestamp",
            datetime(2024, 2, 14, 16, 30, 0, tzinfo=timezone(timedelta(hours=1))),
            id="Central European Time (CET)",
        ),
        pytest.param(
            """<Timestamp>2024-02-14T17:30:00+02:00</Timestamp>""",
            "Timestamp",
            datetime(2024, 2, 14, 17, 30, 0, tzinfo=timezone(timedelta(hours=2))),
            id="Eastern European Time (EET)",
        ),
        pytest.param(
            """<Timestamp>2025-04-11T00:00:00</Timestamp>""",
            "Timestamp",
            datetime(2025, 4, 11, 0, 0, 0, tzinfo=UTC),
            id="Timestamp without timezone info (assumed UTC)",
        ),
    ],
)
def test_parse_timestamp(
    xml_str: str, element_name: str, expected_result: datetime | None
) -> None:
    """
    Test timestamp parsing for various formats and edge cases
    """
    elem = parse_xml_str_as_netex_wrapped(xml_str)
    result = parse_timestamp(elem, element_name)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_str,element_name,expected",
    [
        pytest.param(
            """
            <Container>
              <Name lang="en">English Text</Name>
            </Container>
            """,
            "Name",
            MultilingualString(value="English Text", lang="en"),
            id="Simple English text",
        ),
        pytest.param(
            """
            <Container>
              <Name lang="cy">Welsh Text</Name>
            </Container>
            """,
            "Name",
            MultilingualString(value="Welsh Text", lang="cy"),
            id="Welsh language text",
        ),
        pytest.param(
            """
            <Container>
              <Description lang="en" textIdType="PAS">Pass Description</Description>
            </Container>
            """,
            "Description",
            MultilingualString(value="Pass Description", lang="en", textIdType="PAS"),
            id="Text with ID type",
        ),
        pytest.param(
            """
            <Container>
              <Name>Text without language</Name>
            </Container>
            """,
            "Name",
            MultilingualString(value="Text without language"),
            id="Text without language tag",
        ),
    ],
)
def test_parse_multilingual_string(
    xml_str: str, element_name: str, expected: MultilingualString
) -> None:
    """Test parsing of multilingual strings with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_multilingual_string(elem, element_name)
    assert result is not None

    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str,element_name",
    [
        pytest.param(
            """
            <Container>
              <Name></Name>
            </Container>
            """,
            "Name",
            id="Empty text element",
        ),
        pytest.param(
            """
            <Container>
              <Different>Wrong element</Different>
            </Container>
            """,
            "Name",
            id="Missing named element",
        ),
    ],
)
def test_parse_multilingual_errors(xml_str: str, element_name: str) -> None:
    """Test parsing of multilingual strings with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_multilingual_string(elem, element_name)
    assert result is None


@pytest.mark.parametrize(
    "xml_str,element_name,expected",
    [
        pytest.param(
            """<Root>
                <ColumnRef version="1.0" ref="Trip@AdultSingle-SOP@Line_15@c2@1502" />
            </Root>""",
            "ColumnRef",
            VersionedRef(version="1.0", ref="Trip@AdultSingle-SOP@Line_15@c2@1502"),
            id="Basic versioned reference with version",
        ),
        pytest.param(
            """<Root>
                <ColumnRef versionRef="1.0" ref="Trip@AdultSingle-SOP@Line_15@c2@1502" />
            </Root>""",
            "ColumnRef",
            VersionedRef(version="1.0", ref="Trip@AdultSingle-SOP@Line_15@c2@1502"),
            id="Versioned reference with versionRef attribute",
        ),
        pytest.param(
            """<Root>
                <ColumnRef ref="Trip@AdultSingle-SOP@Line_15@c2@1502" />
            </Root>""",
            "ColumnRef",
            VersionedRef(version=None, ref="Trip@AdultSingle-SOP@Line_15@c2@1502"),
            id="Versioned reference without version",
        ),
    ],
)
def test_parse_versioned_ref(
    xml_str: str, element_name: str, expected: VersionedRef
) -> None:
    """Test parsing of versioned references with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_versioned_ref(elem, element_name)
    assert result is not None
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str,element_name",
    [
        pytest.param(
            """<Root>
                <ColumnRef ref="" />
            </Root>""",
            "ColumnRef",
            id="Empty reference",
        ),
        pytest.param(
            """<Root>
                <ColumnRef />
            </Root>""",
            "ColumnRef",
            id="Missing reference",
        ),
        pytest.param(
            """<Root>
                <UnknownElement ref="Trip@AdultSingle-SOP@Line_15@c2@1502" />
            </Root>""",
            "ColumnRef",
            id="Non-existent element",
        ),
    ],
)
def test_parse_versioned_ref_errors(xml_str: str, element_name: str) -> None:
    """Test parsing of versioned references with invalid inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_versioned_ref(elem, element_name)
    assert result is None
