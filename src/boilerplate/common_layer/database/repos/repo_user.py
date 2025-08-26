"""
SQLAlchemy Users Repos
"""

from structlog.stdlib import get_logger

from ..client import SqlDB
from ..exceptions import (
    DatasetPublishedByUserNotFound,
)
from ..models import (
    UsersUser,
)
from .operation_decorator import handle_repository_errors
from .repo_common import BaseRepositoryWithId

log = get_logger()


class UsersUserRepo(BaseRepositoryWithId[UsersUser]):
    """
    Repository for managing Users entities
    Table: users_user
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, UsersUser)

    @handle_repository_errors
    def require_by_id(self, user_id: int) -> UsersUser:
        """
        Return a Dataset Revision otherwise raise OrganisationDatasetNotFound exception
        """
        user = self.get_by_id(user_id)
        if user is None:
            raise DatasetPublishedByUserNotFound(dataset_id=user_id)
        return user
