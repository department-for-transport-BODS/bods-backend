"""
SQL Alchemy Repos for Table avl_cavldataarchive
"""

from ..client import SqlDB
from ..models.model_avl import AvlCavlDataArchive
from .operation_decorator import handle_repository_errors
from .repo_common import BaseRepository


class AvlCavlDataArchiveRepo(BaseRepository[AvlCavlDataArchive]):
    """
    Repository for managing AvlCavl data archive entities
    Table: pipelines_datasetetltaskresult
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, AvlCavlDataArchive)

    @handle_repository_errors
    def get_by_data_format(self, data_format: str) -> AvlCavlDataArchive | None:
        """
        Get AvlCavlDataArchive by data_format
        """
        statement = self._build_query().where(self._model.data_format == data_format)
        return self._fetch_one(statement)
