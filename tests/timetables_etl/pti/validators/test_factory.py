"""
Test PTI Factory Validator
"""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from pti.app.validators.factory import get_xml_file_pti_validator
from pti.app.validators.xml_file import XmlFilePTIValidator


@patch("pti.validators.factory.PTI_SCHEMA_PATH", new_callable=MagicMock)
@patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
@patch("pti.validators.factory.XmlFilePTIValidator")
def test_get_xml_file_pti_validator(
    mock_validator_class, mock_open_fn, mock_schema_path
):
    """
    Test the `get_xml_file_pti_validator` function.
    """
    m_dynamodb = MagicMock()
    m_db = MagicMock()
    mock_schema_path.return_value = MagicMock(spec=Path)
    mock_open_fn = mock_open(read_data='{"key": "value"}')
    mock_schema_path.open = mock_open_fn

    mock_validator_instance = MagicMock(spec=XmlFilePTIValidator)
    mock_validator_class.return_value = mock_validator_instance

    # Call the function
    result = get_xml_file_pti_validator(dynamodb=m_dynamodb, db=m_db)

    # Assertions
    mock_open_fn.assert_called_once_with("r")
    mock_validator_class.assert_called_once_with(mock_open_fn(), m_dynamodb, m_db)
    assert result == mock_validator_instance
