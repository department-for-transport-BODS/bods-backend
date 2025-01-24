"""
Test XML File
"""

from io import BytesIO
from unittest.mock import MagicMock, patch

from botocore.response import StreamingBody
from common_layer.database.client import SqlDB
from common_layer.dynamodb.client import NaptanStopPointDynamoDBClient
from common_layer.dynamodb.client.cache import DynamoDBCache
from common_layer.txc.models.txc_data import TXCData
from pti.app.validators.xml_file import XmlFilePTIValidator

from tests.factories.database.organisation import OrganisationDatasetRevisionFactory


@patch("pti.app.validators.xml_file.PTIValidator")
def test_get_violations_validates_file(m_pti_validator):
    revision = OrganisationDatasetRevisionFactory(dataset_id=123)
    xml_file = MagicMock(spec=StreamingBody)
    xml_file.read.return_value = b"dummycontent"

    validator = XmlFilePTIValidator(
        schema=BytesIO(),
        dynamodb=MagicMock(spec=DynamoDBCache),
        stop_point_client=MagicMock(spec=NaptanStopPointDynamoDBClient),
        db=MagicMock(spec=SqlDB),
        txc_data=TXCData.model_construct(),
    )
    validator._validator = m_pti_validator.return_value

    m_pti_validator.return_value.violations = ["violation1", "violation2"]

    result = validator.get_violations(revision, xml_file)

    assert result == ["violation1", "violation2"]
    validator._validator.is_valid.assert_called_once_with(xml_file)
