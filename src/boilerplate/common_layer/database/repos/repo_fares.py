"""
SQL Alchemy Repos for Tables prefixed with fares_
"""

from common_layer.database.repos.operation_decorator import handle_repository_errors
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import delete

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
            statement = delete(FaresMetadata).where(
                self._model.datasetmetadata_ptr_id == metadata_id
            )
            result = session.execute(statement)

            return result.rowcount > 0

    @handle_repository_errors
    def update_metadata(self, metadata: FaresMetadata) -> bool:
        """
        Update metadata
        """
        with self._db.session_scope() as session:
            statement = insert(FaresMetadata).values([metadata])
            statement = statement.on_conflict_do_update(
                index_elements=[FaresMetadata.datasetmetadata_ptr_id],
                set_=dict(
                    num_of_fare_zones=statement.excluded.num_of_fare_zones
                    + FaresMetadata.num_of_fare_zones,
                    num_of_lines=statement.excluded.num_of_lines
                    + FaresMetadata.num_of_lines,
                    num_of_sales_offer_packages=statement.excluded.num_of_sales_offer_packages
                    + FaresMetadata.num_of_sales_offer_packages,
                    num_of_fare_products=statement.excluded.num_of_fare_products
                    + FaresMetadata.num_of_fare_products,
                    num_of_user_profiles=statement.excluded.num_of_user_profiles
                    + FaresMetadata.num_of_user_profiles,
                    valid_from=text(
                        "least(excluded.valid_from, fares_faresmetadata.valid_from::timestamptz)"
                    ),
                    valid_to=text(
                        "greatest(excluded.valid_to, fares_faresmetadata.valid_to::timestamptz)"
                    ),
                    num_of_pass_products=statement.excluded.num_of_pass_products
                    + FaresMetadata.num_of_pass_products,
                    num_of_trip_products=statement.excluded.num_of_trip_products
                    + FaresMetadata.num_of_trip_products,
                ),
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

    def __init__(self, db: SqlDB):
        super().__init__(db, FaresDataCatalogueMetadata)

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

    def __init__(self, db: SqlDB):
        super().__init__(db, FaresValidation)


class FaresValidationResultRepo(BaseRepositoryWithId[FaresValidationResult]):
    """
    Repository for managing Fares Validation Results
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, FaresValidationResult)
