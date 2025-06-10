"""
PTI Validators Conftest
"""

from io import BytesIO, StringIO
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from common_layer.database.client import SqlDB
from common_layer.dynamodb.client import NaptanStopPointDynamoDBClient
from common_layer.dynamodb.client.cache import DynamoDBCache
from common_layer.xml.txc.models.txc_data import TXCData
from pti.app.constants import PTI_SCHEMA_PATH
from pti.app.models.models_pti import PtiJsonSchema
from pti.app.models.models_pti_task import DbClients
from pti.app.pti_validation import get_txc_data
from pti.app.validators.pti import PTIValidator

from tests.timetables_etl.pti.validators.constants import TXC_END, TXC_START


class XMLFile(BytesIO):
    def __init__(self, str_: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.write(str_.encode("utf-8"))
        self.name = "file.xml"
        self.seek(0)


class TXCFile(XMLFile):
    def __init__(self, str_: str, **kwargs: Any) -> None:
        s = TXC_START + str_ + TXC_END
        super().__init__(s, **kwargs)
        self.name = "txc.xml"


class JSONFile(StringIO):
    def __init__(self, str_: str, **kwargs: Any) -> None:
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


def load_txc_data_from_fixture(
    data_dir: Path,
    filename: str,
) -> TXCData:

    fixture_path = data_dir / filename
    with open(fixture_path, "rb") as test_file:
        test_file_bytes = BytesIO(test_file.read())
        txc_data = get_txc_data(test_file_bytes)
        return txc_data


def create_validator(
    filename: str | None,
    data_dir: Path | None,
    observation_id: int,
    naptan_stop_point_client: NaptanStopPointDynamoDBClient | None = None,
) -> PTIValidator:
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

    txc_data = (
        load_txc_data_from_fixture(data_dir, filename)
        if (filename and data_dir)
        else TXCData.model_construct()
    )

    pti = PTIValidator(
        json_file,
        db_clients,
        txc_data,
    )
    return pti


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
    pti = create_validator(filename, data_dir, observation_id, naptan_stop_point_client)
    txc_path = data_dir / filename
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
    pti = create_validator(filename, data_dir, observation_id, None)
    txc_path = data_dir / filename
    with txc_path.open("rb") as f:
        content = BytesIO(f.read())
        with pytest.raises(expected_exception, match=match):
            pti.is_valid(content)
