from ..models import (
    FaresDataCatalogueMetadata,
    FaresMetadata,
    FaresMetadataStops,
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


class FaresMetadataStopsRepo(BaseRepositoryWithId[FaresMetadataStops]):
    """
    Repository for managing Fares Metadata Stops
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, FaresMetadataStops)


class FaresDataCatalogueMetadataRepo(BaseRepositoryWithId[FaresDataCatalogueMetadata]):
    """
    Repository for managing Fares Data Catalogue Metadata
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, FaresDataCatalogueMetadata)


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
