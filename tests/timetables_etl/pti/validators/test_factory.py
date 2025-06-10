"""
Test PTI Factory Validator
"""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from common_layer.database.client import SqlDB
from common_layer.dynamodb.client.cache import DynamoDBCache
from common_layer.dynamodb.client.naptan_stop_points import (
    NaptanStopPointDynamoDBClient,
)
from common_layer.xml.txc.models.txc_data import TXCData
from pti.app.models.models_pti_task import DbClients
from pti.app.validators.factory import get_xml_file_pti_validator
from pti.app.validators.xml_file import XmlFilePTIValidator


@patch("pti.app.validators.factory.PTI_SCHEMA_PATH", new_callable=MagicMock)
@patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
@patch("pti.app.validators.factory.XmlFilePTIValidator")
def test_get_xml_file_pti_validator(
    mock_validator_class: MagicMock,
    mock_open_fn: MagicMock,
    mock_schema_path: MagicMock,
) -> None:
    """
    Test the `get_xml_file_pti_validator` function initializes and returns
    the XmlFilePTIValidator with the expected arguments
    """
    m_dynamodb = MagicMock(spec=DynamoDBCache)
    m_stop_point_client = MagicMock(spec=NaptanStopPointDynamoDBClient)
    m_db = MagicMock(spec=SqlDB)
    clients = DbClients(
        sql_db=m_db, dynamodb=m_dynamodb, stop_point_client=m_stop_point_client
    )

    txc_data = TXCData.model_construct()
    mock_schema_path.return_value = MagicMock(spec=Path)
    mock_open_fn = mock_open(read_data='{"key": "value"}')
    mock_schema_path.open = mock_open_fn

    mock_validator_instance = MagicMock(spec=XmlFilePTIValidator)
    mock_validator_class.return_value = mock_validator_instance

    result = get_xml_file_pti_validator(
        db_clients=clients,
        txc_data=txc_data,
    )

    # Assertions
    mock_open_fn.assert_called_once_with("r")
    mock_validator_class.assert_called_once_with(mock_open_fn(), clients, txc_data)
    assert result == mock_validator_instance
