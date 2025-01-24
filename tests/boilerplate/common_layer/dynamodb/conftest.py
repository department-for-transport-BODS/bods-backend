from unittest.mock import patch

import pytest


@pytest.fixture()
def m_boto_client():
    with patch("common_layer.dynamodb.client.base.boto3.client") as m_boto:
        yield m_boto.return_value
