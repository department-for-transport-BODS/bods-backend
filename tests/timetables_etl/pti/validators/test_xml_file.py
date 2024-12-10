import pytest
from unittest.mock import MagicMock, patch
from io import BytesIO
from botocore.response import StreamingBody

from pti.validators.xml_file import XmlFilePTIValidator


@patch("pti.validators.xml_file.PTIValidator")
def test_get_violations_validates_file(m_pti_validator):
    revision = MagicMock(dataset_id=123)
    xml_file = MagicMock(spec=StreamingBody)
    xml_file.read.return_value = b"dummycontent"

    m_pti_validator.return_value.is_valid = MagicMock()
    m_pti_validator.return_value.violations = ["violation1", "violation2"]

    validator = XmlFilePTIValidator(schema=BytesIO(), dynamodb=MagicMock())

    result = validator.get_violations(revision, xml_file)

    assert result == ["violation1", "violation2"]
    validator._validator.is_valid.assert_called_once()
