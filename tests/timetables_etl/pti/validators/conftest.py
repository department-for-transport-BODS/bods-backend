from io import BytesIO, StringIO
from pathlib import Path
from unittest.mock import MagicMock

from common_layer.pti.models import Schema
from pti.app.constants import PTI_SCHEMA_PATH
from pti.app.validators.pti import PTIValidator

from tests.timetables_etl.pti.validators.constants import TXC_END, TXC_START


class XMLFile(BytesIO):
    def __init__(self, str_, **kwargs):
        super().__init__(**kwargs)
        self.write(str_.encode("utf-8"))
        self.name = "file.xml"
        self.seek(0)


class TXCFile(XMLFile):
    def __init__(self, str_, **kwargs):
        s = TXC_START + str_ + TXC_END
        super().__init__(s, **kwargs)
        self.name = "txc.xml"


class JSONFile(StringIO):
    def __init__(self, str_, **kwargs):
        super().__init__(**kwargs)
        self.write(str_)
        self.seek(0)
        self.name = "pti_schema.json"


def create_validator(
    filename: str, data_dir: Path, observation_id: int
) -> tuple[PTIValidator, Path]:
    """
    Helper function to create PTIValidator instance and file path
    """
    schema = Schema.from_path(PTI_SCHEMA_PATH)
    observations = [o for o in schema.observations if o.number == observation_id]
    schema.observations = observations
    json_file = JSONFile(schema.model_dump_json())
    pti = PTIValidator(json_file, MagicMock(), MagicMock())
    return pti, data_dir / filename


def run_validation(filename: str, data_dir: Path, observation_id: int) -> bool:
    """
    Run PTI validation on a file

    Returns whether it was successful
    """
    pti, txc_path = create_validator(filename, data_dir, observation_id)
    with txc_path.open("rb") as f:
        content = BytesIO(f.read())
        return pti.is_valid(content)
