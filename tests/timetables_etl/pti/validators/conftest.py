from io import BytesIO, StringIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from common_layer.database.client import SqlDB
from common_layer.dynamodb.client import DynamoDB, NaptanStopPointDynamoDBClient
from common_layer.dynamodb.client.cache import DynamoDBCache, DynamoDbCacheSettings
from common_layer.xml.txc.models.txc_data import TXCData
from pti.app.constants import PTI_SCHEMA_PATH
from pti.app.models.models_pti import PtiJsonSchema
from pti.app.models.models_pti_task import DbClients
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


def setup_stop_point_client() -> MagicMock:
    m_stop_point_client = MagicMock(spec=NaptanStopPointDynamoDBClient)
    m_stop_point_client.get_by_atco_codes.return_value = (
        [],
        [],
    )
    return m_stop_point_client


def create_validator(
    filename: str,
    data_dir: Path,
    observation_id: int,
    naptan_stop_point_client: NaptanStopPointDynamoDBClient | None = None,
) -> tuple[PTIValidator, Path]:
    """
    Helper function to create PTIValidator instance and file path
    """
    schema = PtiJsonSchema.from_path(PTI_SCHEMA_PATH)
    observations = [o for o in schema.observations if o.number == observation_id]
    schema.observations = observations
    json_file = JSONFile(schema.model_dump_json())

    stop_point_client = naptan_stop_point_client or setup_stop_point_client()
    db_clients = DbClients(
        sql_db=MagicMock(spec=SqlDB),
        dynamodb=MagicMock(spec=DynamoDBCache),
        stop_point_client=stop_point_client,
    )
    pti = PTIValidator(
        json_file,
        db_clients,
        TXCData.model_construct(),
    )
    return pti, data_dir / filename


def run_validation(
    filename: str,
    data_dir: Path,
    observation_id: int,
    naptan_stop_point_client: NaptanStopPointDynamoDBClient | None = None,
) -> bool:
    """
    Run PTI validation on a file

    Returns whether it was successful
    """
    pti, txc_path = create_validator(
        filename, data_dir, observation_id, naptan_stop_point_client
    )
    with txc_path.open("rb") as f:
        content = BytesIO(f.read())
        return pti.is_valid(content)


def run_validation_with_exception(
    filename: str,
    data_dir: Path,
    observation_id: int,
    expected_exception: type[Exception],
    match: str,
) -> None:
    """
    Run PTI validation on a file, expecting an exception
    """
    pti, txc_path = create_validator(filename, data_dir, observation_id)
    with txc_path.open("rb") as f:
        content = BytesIO(f.read())
        with pytest.raises(expected_exception, match=match):
            pti.is_valid(content)
