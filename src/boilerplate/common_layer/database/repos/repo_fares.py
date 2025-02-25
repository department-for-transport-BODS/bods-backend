"""
SQL Alchemy Repos for Tables prefixed with fares_
"""

from typing import cast

from common_layer.database.repos.operation_decorator import handle_repository_errors
from sqlalchemy import Table, delete

from ..models import (
    FaresDataCatalogueMetadata,
    FaresMetadata,
    FaresMetadataStop,
    FaresValidation,
    FaresValidationResult,
)
from .repo_common import BaseRepository, BaseRepositoryWithId, SqlDB


class FaresMetadataRepo(BaseRepository[FaresMetadata]):
    """
    Repository for managing Fares Metadata
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, FaresMetadata)

    @handle_repository_errors
    def delete_by_metadata_id(self, metadata_id: int) -> bool:
        """
        Delete by metadata id
        """
        with self._db.session_scope() as session:
            statement = delete(cast(Table, self._model.__table__)).where(
                self._model.datasetmetadata_ptr_id == metadata_id
            )
            result = session.execute(statement)

            return result.rowcount > 0


class FaresMetadataStopsRepo(BaseRepositoryWithId[FaresMetadataStop]):
    """
    Repository for managing Fares Metadata Stops
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, FaresMetadataStop)

    @handle_repository_errors
    def delete_by_metadata_id(self, metadata_id: int) -> bool:
        """
        Delete by metadata id
        """
        with self._db.session_scope() as session:
            statement = delete(cast(Table, self._model.__table__)).where(
                self._model.faresmetadata_id == metadata_id
            )
            result = session.execute(statement)

            return result.rowcount > 0


class FaresDataCatalogueMetadataRepo(BaseRepositoryWithId[FaresDataCatalogueMetadata]):
    """
    Repository for managing Fares Data Catalogue Metadata
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, FaresDataCatalogueMetadata)

    @handle_repository_errors
    def delete_by_metadata_id(self, metadata_id: int) -> bool:
        """
        Delete by metadata id
        """
        with self._db.session_scope() as session:
            statement = delete(cast(Table, self._model.__table__)).where(
                self._model.fares_metadata_id == metadata_id
            )
            result = session.execute(statement)

            return result.rowcount > 0


class FaresValidationRepo(BaseRepositoryWithId[FaresValidation]):
    """
    Repository for managing Fares Validation
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, FaresValidation)


class FaresValidationResultRepo(BaseRepositoryWithId[FaresValidationResult]):
    """
    Repository for managing Fares Validation Results
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, FaresValidationResult)
