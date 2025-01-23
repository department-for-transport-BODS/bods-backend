"""
Test XML File
"""

from io import BytesIO
from unittest.mock import MagicMock, patch

from botocore.response import StreamingBody
from pti.app.validators.xml_file import XmlFilePTIValidator


@patch("pti.app.validators.xml_file.PTIValidator")
def test_get_violations_validates_file(m_pti_validator):
    revision = MagicMock(dataset_id=123)
    xml_file = MagicMock(spec=StreamingBody)
    xml_file.read.return_value = b"dummycontent"

    validator = XmlFilePTIValidator(
        schema=BytesIO(), dynamodb=MagicMock(), db=MagicMock()
    )
    validator._validator = m_pti_validator.return_value

    m_pti_validator.return_value.violations = ["violation1", "violation2"]

    result = validator.get_violations(revision, xml_file)

    assert result == ["violation1", "violation2"]
    validator._validator.is_valid.assert_called_once_with(xml_file)
