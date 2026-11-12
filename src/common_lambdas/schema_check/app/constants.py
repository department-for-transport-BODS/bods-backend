"""
Constants related to Schema Check
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple


class TXCVersion(Enum):
    """Supported TransXChange schema versions."""

    V2_4 = "2.4"


class NeTExVersion(Enum):
    """Supported NeTEx schema versions."""

    V1_1 = "1.1"


class XMLDataType(Enum):
    """Supported Data Types."""

    TIMETABLES = "timetables"
    FARES = "fares"


class XMLSchemaType(Enum):
    """Supported Schema Types."""

    TRANSXCHANGE = "TXC"
    NETEX = "Netex"


@dataclass(frozen=True)
class SchemaSpec:
    """
    Model to build the path to load an XML schema from the local file system
    """

    version_enum: Enum
    schema_type: XMLSchemaType
    filename: str


# Supported Schema Specs by SchemaType and Version
SCHEMA_SPECS: Dict[Tuple[XMLSchemaType, str], SchemaSpec] = {
    (XMLSchemaType.TRANSXCHANGE, "2.4"): SchemaSpec(
        TXCVersion.V2_4,
        XMLSchemaType.TRANSXCHANGE,
        "TransXChange_general.xsd",
    ),
    (XMLSchemaType.NETEX, "1.1"): SchemaSpec(
        NeTExVersion.V1_1,
        XMLSchemaType.NETEX,
        "NeTEx_publication.xsd",
    ),
}
