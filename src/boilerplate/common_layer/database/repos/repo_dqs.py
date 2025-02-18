from common_layer.database.client import SqlDB
from common_layer.database.models.model_data_quality import DataQualityPTIObservation
from common_layer.database.models.model_dqs import DQSTaskResults
from common_layer.database.repos.operation_decorator import handle_repository_errors
from common_layer.database.repos.repo_common import BaseRepositoryWithId
from common_layer.dynamodb.models import TXCFileAttributes
from sqlalchemy import Select


class DQSTaskResultsRepo(BaseRepositoryWithId[DQSTaskResults]):
    """
    DQSTaskResults Repository
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, DQSTaskResults)

    @handle_repository_errors
    def delete_all_by_txc_file_attributes_ids(
        self, txc_file_attribute_ids_query: Select[tuple[int]]
    ) -> int:
        """
        Delete all DQSTaskResults for the given txc_file_attributes_ids_query

        :param: txc_file_attribute_ids_query: Select statement returning TXCFileAttributes IDs.

        Returns: Number of deleted records.
        """
        delete_statement = self._build_delete_query().where(
            self._model.transmodel_txcfileattributes_id.in_(
                txc_file_attribute_ids_query
            )
        )
        return self._delete_all(delete_statement)
