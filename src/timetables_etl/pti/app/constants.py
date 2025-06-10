"""
Constants
"""

from pathlib import Path

PTI_SCHEMA_PATH: Path = Path(__file__).parent / "pti_schema.json"
NAMESPACE: dict[str, str] = {"x": "http://www.transxchange.org.uk/"}
