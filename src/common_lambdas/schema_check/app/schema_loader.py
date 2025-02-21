"""
Functions for loading an XMLSchema for validation purposes
"""

from pathlib import Path

from lxml.etree import ParseError, XMLParser, XMLSchema, XMLSchemaParseError, parse
from structlog.stdlib import get_logger

from .constants import SCHEMA_SPECS, SchemaSpec, XMLSchemaType

log = get_logger()


def get_schema_spec(schema_type: XMLSchemaType, version: str) -> SchemaSpec:
    """
    Retrieve the schema spec for a given schema type and version.
    """
    schema_spec = SCHEMA_SPECS.get((schema_type, version))
    if not schema_spec:
        log.error(
            "Unsupported schema type/version", schema_type=schema_type, version=version
        )
        raise ValueError(
            f"Unsupported schema type '{schema_type.value}' with version '{version}'"
        )

    return schema_spec


def load_schema(schema_type: XMLSchemaType, version: str) -> XMLSchema:
    """
    Load an XML schema using the given schema type and version.
    Returns: Loaded XMLSchema object
    """
    schema_spec = get_schema_spec(schema_type, version)

    schema_path = (
        Path(__file__).parent
        / "schemas"
        / schema_spec.schema_type.value.lower()
        / schema_spec.version_enum.value
        / schema_spec.filename
    )

    if not schema_path.exists():
        log.error(
            "Schema file not Found",
            schema_path=schema_path,
        )
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")

    try:
        parser = XMLParser(load_dtd=False, no_network=True)
        with open(schema_path, "rb") as schema_file:
            schema_doc = parse(schema_file, parser)
            log.debug("Parsed Schema Doc as _ElementTree[_Element]")
            schema = XMLSchema(schema_doc)
            log.info("Successfully parsed Schema Doc as XMLSchema")
            return schema
    except (XMLSchemaParseError, ParseError) as e:
        log.error("schema_parse_error", error=str(e))
        raise
