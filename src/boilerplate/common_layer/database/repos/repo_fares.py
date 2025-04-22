"""
SQL Alchemy Repos for Tables prefixed with fares_
"""

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import delete

from ..models import (
    FaresDataCatalogueMetadata,
    FaresMetadata,
    FaresMetadataStop,
    FaresValidation,
    FaresValidationResult,
)
from .operation_decorator import handle_repository_errors
from .repo_common import BaseRepository, BaseRepositoryWithId, SqlDB


class FaresMetadataRepo(BaseRepository[FaresMetadata]):
    """
    Repository for managing Fares Metadata
    """

    def __init__(self, db: SqlDB) -> None:
        super().__init__(db, FaresMetadata)

    @handle_repository_errors
    def get_by_metadata_id(self, metadata_id: int) -> FaresMetadata | None:
        """
        Retrieve a FaresMetadata by its metadata id (datasetmetadata_ptr_id)
        """
        statement = self._build_query().where(
            self._model.datasetmetadata_ptr_id == metadata_id
        )
        return self._fetch_one(statement)

    @handle_repository_errors
    def delete_by_metadata_id(self, metadata_id: int) -> bool:
        """
        Delete by metadata id
        """
        with self._db.session_scope() as session:
            statement = delete(FaresMetadata).where(
                self._model.datasetmetadata_ptr_id == metadata_id
            )
            result = session.execute(statement)

            return result.rowcount > 0


class FaresMetadataStopsRepo(BaseRepositoryWithId[FaresMetadataStop]):
    """
    Repository for managing Fares Metadata Stops
    """

    def __init__(self, db: SqlDB) -> None:
        super().__init__(db, FaresMetadataStop)

    @handle_repository_errors
    def get_by_metadata_id(self, metadata_id: int) -> list[FaresMetadataStop]:
        """
        Retrieve all FaresMetadataStop for a specific metadata id
        """
        statement = self._build_query().where(
            self._model.faresmetadata_id == metadata_id
        )
        return self._fetch_all(statement)

    @handle_repository_errors
    def delete_by_metadata_id(self, metadata_id: int) -> bool:
        """
        Delete by metadata id
        """
        with self._db.session_scope() as session:
            statement = delete(FaresMetadataStop).where(
                self._model.faresmetadata_id == metadata_id
            )
            result = session.execute(statement)

            return result.rowcount > 0

    @handle_repository_errors
    def batch_insert_stops(self, stops: list[FaresMetadataStop]) -> bool:
        """
        Batch insert stops
        """
        with self._db.session_scope() as session:
            statement = insert(FaresMetadataStop).values(stops)
            statement = statement.on_conflict_do_update(
                index_elements=[
                    FaresMetadataStop.faresmetadata_id,
                    FaresMetadataStop.stoppoint_id,
                ]
            )

            result = session.execute(statement)

            return result.rowcount > 0


class FaresDataCatalogueMetadataRepo(BaseRepositoryWithId[FaresDataCatalogueMetadata]):
    """
    Repository for managing Fares Data Catalogue Metadata
    """

    def __init__(self, db: SqlDB) -> None:
        super().__init__(db, FaresDataCatalogueMetadata)

    @handle_repository_errors
    def get_by_metadata_id(self, metadata_id: int) -> list[FaresDataCatalogueMetadata]:
        """
        Retrieve all FaresDataCatalogueMetadata for a specific metadata id
        """
        statement = self._build_query().where(
            self._model.fares_metadata_id == metadata_id
        )
        return self._fetch_all(statement)

    @handle_repository_errors
    def delete_by_metadata_id(self, metadata_id: int) -> bool:
        """
        Delete by metadata id
        """
        with self._db.session_scope() as session:
            statement = delete(FaresDataCatalogueMetadata).where(
                self._model.fares_metadata_id == metadata_id
            )
            result = session.execute(statement)

            return result.rowcount > 0


class FaresValidationRepo(BaseRepositoryWithId[FaresValidation]):
    """
    Repository for managing Fares Validation
    """

    def __init__(self, db: SqlDB) -> None:
        super().__init__(db, FaresValidation)

    @handle_repository_errors
    def get_by_revision_id(self, revision_id: int) -> list[FaresValidation]:
        """
        Retrieve all FaresValidation for a specific revision
        """
        statement = self._build_query().where(self._model.revision_id == revision_id)
        return self._fetch_all(statement)

    @handle_repository_errors
    def delete_by_revision_id(self, revision_id: int) -> bool:
        """
        Delete by revision id
        """
        with self._db.session_scope() as session:
            statement = delete(FaresValidation).where(
                self._model.revision_id == revision_id
            )
            result = session.execute(statement)

            return result.rowcount > 0


class FaresValidationResultRepo(BaseRepositoryWithId[FaresValidationResult]):
    """
    Repository for managing Fares Validation Results
    """

    def __init__(self, db: SqlDB) -> None:
        super().__init__(db, FaresValidationResult)

    @handle_repository_errors
    def get_by_revision_id(self, revision_id: int) -> list[FaresValidationResult]:
        """
        Retrieve all FaresValidationResult for a specific revision
        """
        statement = self._build_query().where(self._model.revision_id == revision_id)
        return self._fetch_all(statement)

    @handle_repository_errors
    def delete_by_revision_id(self, revision_id: int) -> bool:
        """
        Delete by revision id
        """
        with self._db.session_scope() as session:
            statement = delete(FaresValidationResult).where(
                self._model.revision_id == revision_id
            )
            result = session.execute(statement)

            return result.rowcount > 0
