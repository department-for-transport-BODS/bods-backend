"""
PtiValidation Lambda Task Models
"""

from io import BytesIO

from attr import dataclass
from common_layer.database.client import SqlDB
from common_layer.database.models import OrganisationDatasetRevision
from common_layer.dynamodb.client.cache import DynamoDBCache
from common_layer.dynamodb.client.naptan_stop_points import (
    NaptanStopPointDynamoDBClient,
)
from common_layer.dynamodb.models import TXCFileAttributes
from common_layer.xml.txc.models import TXCData
from pydantic import BaseModel, ConfigDict


class PTITaskData(BaseModel):
    """
    Task Data Container
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    revision: OrganisationDatasetRevision
    txc_file_attributes: TXCFileAttributes
    live_txc_file_attributes: list[TXCFileAttributes]
    xml_file_object: BytesIO
    txc_data: TXCData


@dataclass
class DbClients:
    """
    DB Clients Container
    """

    sql_db: SqlDB
    dynamodb: DynamoDBCache
    stop_point_client: NaptanStopPointDynamoDBClient
