import pytest
from unittest.mock import MagicMock, patch
from io import BytesIO
from botocore.response import StreamingBody

from pti.validators.xml_file import XmlFilePTIValidator


def test_get_violations_validates_file():
    revision = MagicMock(dataset_id=123)
    xml_file = MagicMock(spec=StreamingBody)
    xml_file.read.return_value = b"dummycontent"

    validator = XmlFilePTIValidator(schema=BytesIO())
    validator._validator.is_valid = MagicMock()
    validator._validator.violations = ["violation1", "violation2"]

    result = validator.get_violations(revision, xml_file)

    assert result == ["violation1", "violation2"]
    validator._validator.is_valid.assert_called_once()
