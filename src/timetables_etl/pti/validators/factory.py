from pathlib import Path

from timetables_etl.pti.validators.xml_file import XmlFilePTIValidator

# TODO: Add this static file
PTI_SCHEMA_PATH = Path(__file__) / "pti_schema.json"

def get_xml_file_pti_validator() -> XmlFilePTIValidator:
    """
    Gets a PTI JSON Schema and returns a DatasetPTIValidator.
    """
    with PTI_SCHEMA_PATH.open("r") as f:
        validator = XmlFilePTIValidator(f)
    return validator