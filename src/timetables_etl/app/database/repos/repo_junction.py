"""
Repos for Many to Many Relationhip Tables
AKA: Associative Entity, Junction Tables, Jump Tables
"""

from typing import NamedTuple

from sqlalchemy import select

from ..models import TransmodelServiceServicePattern
from .repo_common import BaseRepository, BodsDB, handle_repository_errors


class ServicePatternAssociation(NamedTuple):
    """
    Association between a service_id and pattern_id to create
    """

    service_id: int
    pattern_id: int


class TransmodelServiceServicePatternRepo(
    BaseRepository[TransmodelServiceServicePattern]
):
    """
    Repository for managing Service-ServicePattern associations
    transmodel_service_service_patterns
    """

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelServiceServicePattern)

    @handle_repository_errors
    def get_by_service_id(
        self, service_id: int
    ) -> list[TransmodelServiceServicePattern]:
        """
        Get transmodel_service pattern rows mapped to a row in transmodel_service
        """
        statement = select(self._model).where(self._model.service_id == service_id)
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_service_ids(
        self, service_ids: list[int]
    ) -> list[TransmodelServiceServicePattern]:
        """
        Get transmodel_servicepattern rows mapped to a list of transmodel_service row ids
        """
        statement = select(self._model).where(self._model.service_id.in_(service_ids))
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_pattern_id(
        self, pattern_id: int
    ) -> list[TransmodelServiceServicePattern]:
        """
        Get transmodel_services mapped to a transmodel_servicepattern
        """
        statement = select(self._model).where(
            self._model.servicepattern_id == pattern_id
        )
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_pattern_ids(
        self, pattern_ids: list[int]
    ) -> list[TransmodelServiceServicePattern]:
        """
        Get Services mapped to a list of transmodel_servicepattern row ids
        """
        statement = select(self._model).where(
            self._model.servicepattern_id.in_(pattern_ids)
        )
        return self._fetch_all(statement)

    @handle_repository_errors
    def add_association(
        self, service_id: int, pattern_id: int
    ) -> TransmodelServiceServicePattern:
        """
        Add Association between service and pattern and return the created record
        """
        with self._db.session_scope() as session:
            association = TransmodelServiceServicePattern(
                service_id=service_id, servicepattern_id=pattern_id
            )
            session.add(association)
            session.flush()
            return association

    @handle_repository_errors
    def add_associations(
        self, associations: list[ServicePatternAssociation]
    ) -> list[TransmodelServiceServicePattern]:
        """
        Bulk insert multiple service-pattern associations and return the created records
        """
        with self._db.session_scope() as session:
            records = [
                TransmodelServiceServicePattern(
                    service_id=assoc.service_id, servicepattern_id=assoc.pattern_id
                )
                for assoc in associations
            ]
            session.bulk_save_objects(records)
            session.flush()
            return records
