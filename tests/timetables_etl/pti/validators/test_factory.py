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
from common_layer.txc.models.txc_data import TXCData
from pti.app.validators.factory import get_xml_file_pti_validator
from pti.app.validators.xml_file import XmlFilePTIValidator


@patch("pti.app.validators.factory.PTI_SCHEMA_PATH", new_callable=MagicMock)
@patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
@patch("pti.app.validators.factory.XmlFilePTIValidator")
def test_get_xml_file_pti_validator(
    mock_validator_class, mock_open_fn, mock_schema_path
):
    """
    Test the `get_xml_file_pti_validator` function initializes and returns
    the XmlFilePTIValidator with the expected arguments
    """
    m_dynamodb = MagicMock(spec=DynamoDBCache)
    m_stop_point_client = MagicMock(spec=NaptanStopPointDynamoDBClient)
    m_db = MagicMock(spec=SqlDB)
    txc_data = TXCData.model_construct()
    mock_schema_path.return_value = MagicMock(spec=Path)
    mock_open_fn = mock_open(read_data='{"key": "value"}')
    mock_schema_path.open = mock_open_fn

    mock_validator_instance = MagicMock(spec=XmlFilePTIValidator)
    mock_validator_class.return_value = mock_validator_instance

    result = get_xml_file_pti_validator(
        dynamodb=m_dynamodb,
        stop_point_client=m_stop_point_client,
        db=m_db,
        txc_data=txc_data,
    )

    # Assertions
    mock_open_fn.assert_called_once_with("r")
    mock_validator_class.assert_called_once_with(
        mock_open_fn(), m_dynamodb, m_stop_point_client, m_db, txc_data
    )
    assert result == mock_validator_instance
