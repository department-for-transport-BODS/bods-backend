"""
Tests for schema loading
"""

import inspect
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from common_layer.exceptions import SchemaUnknown
from lxml.etree import Resolver, XMLParser, XMLSchema, _ElementTree, parse  # type: ignore

from common_lambdas.schema_check.app.constants import XMLSchemaType
from common_lambdas.schema_check.app.schema_loader import load_schema

MODULE_PATH = Path(inspect.getfile(load_schema)).parent


class OfflineSchemaResolver(Resolver):
    """Make network-dependent schema imports fail regardless of local XML catalogs."""

    def resolve(self, url, pubid, context):
        if url.startswith(("http://", "https://")):
            raise OSError(f"Remote schema dependency is not packaged: {url}")
        return None


@pytest.mark.parametrize("version", ["2.4", "2.4.1"])
def test_packaged_txc_schema_compiles_offline(version: str) -> None:
    """Compile the real schema dependency tree without remote resources."""
    parser = XMLParser(load_dtd=False, no_network=True)
    parser.resolvers.add(OfflineSchemaResolver())
    schema_path = MODULE_PATH / "schemas" / "txc" / version / "TransXChange_general.xsd"

    schema = XMLSchema(parse(str(schema_path), parser))

    assert isinstance(schema, XMLSchema)


@pytest.fixture
def m_valid_schema_file():
    """
    Mock a valid XML schema file content.
    """
    return b'<?xml version="1.0" encoding="UTF-8"?><xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"></xs:schema>'


@pytest.fixture
def setup_mocks(mocker, m_valid_schema_file: bytes):
    """
    Setup mocks for schema loading
    """
    m_path = mocker.patch(
        "common_lambdas.schema_check.app.schema_loader.Path.exists", return_value=True
    )
    m_open = mocker.patch("builtins.open", mock_open(read_data=m_valid_schema_file))
    m_parse = mocker.patch(
        "common_lambdas.schema_check.app.schema_loader.parse",
        return_value=_ElementTree(),
    )
    m_xml_schema = mocker.patch(
        "common_lambdas.schema_check.app.schema_loader.XMLSchema"
    )

    return m_open, m_xml_schema


@pytest.mark.parametrize(
    "inputs, expected_file_name",
    [
        ((XMLSchemaType.TRANSXCHANGE, "2.4"), "TransXChange_general.xsd"),
        ((XMLSchemaType.TRANSXCHANGE, "2.4.1"), "TransXChange_general.xsd"),
        ((XMLSchemaType.NETEX, "1.1"), "NeTEx_publication.xsd"),
    ],
)
def test_load_schema_valid(setup_mocks, inputs, expected_file_name):
    """
    Test that load_schema correctly looks for the schema file in the expected path and returns the parsed XMLSchema.
    """
    schema_type, version = inputs
    m_open, m_xml_schema = setup_mocks

    expected_path = (
        MODULE_PATH
        / "schemas"
        / schema_type.value.lower()
        / version
        / expected_file_name
    )

    result = load_schema(schema_type, version)

    assert result == m_xml_schema.return_value
    m_open.assert_called_once_with(
        expected_path, "rb"
    )  # Schema sourced from expected path


@pytest.mark.parametrize(
    "schema_type, version",
    [
        pytest.param(XMLSchemaType.TRANSXCHANGE, "3.0", id="Unsupported TXC Version"),
        pytest.param(XMLSchemaType.NETEX, "2.0", id="Unsupported Netex Version"),
    ],
)
def test_load_schema_invalid_version(schema_type: XMLSchemaType, version: str) -> None:
    """
    Test that load_schema raises a ValueError when given an unsupported schema type/version.
    """
    with pytest.raises(
        SchemaUnknown,
    ):
        load_schema(schema_type, version)


def test_load_schema_missing_file():
    """
    Test that load_schema raises FileNotFoundError if the schema file does not exist.
    """
    schema_type, version = XMLSchemaType.TRANSXCHANGE, "2.4"

    with patch(
        "common_lambdas.schema_check.app.schema_loader.Path.exists", return_value=False
    ):
        with pytest.raises(FileNotFoundError, match="Schema file not found at:"):
            load_schema(schema_type, version)
