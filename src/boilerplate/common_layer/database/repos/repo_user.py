"""
SQLAlchemy Users Repos
"""

from typing import List

from common_layer.database.models.model_organisation import (
    OrganisationDatasetSubscription,
)
from structlog.stdlib import get_logger

from ..client import SqlDB
from ..exceptions import (
    DatasetPublishedByUserNotFound,
)
from ..models import AgentUserInvite, UserSettings, UsersUser
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

    @handle_repository_errors
    def fetch_agents_for_org(self, org_id: int) -> List[UsersUser]:
        """Method will fetch agent users who has accepted the invitation
        for the organisation id

        Args:
            org_id (int): Organisation id for which we are searching agents

        Returns:
            List[UsersUser]: List of all the agent users
        """
        statement = (
            self._build_query()
            .join(AgentUserInvite, AgentUserInvite.agent_id == self._model.id)
            .where(AgentUserInvite.organisation_id == org_id)
        )
        return self._fetch_all(statement)

    @handle_repository_errors
    def fetch_dataset_subscribers(self, dataset_id: int) -> List[UsersUser]:
        """Users who has subscribed to the dataset

        Args:
            dataset_id (int): Id of the dataset

        Returns:
            List[UsersUser]: List of users who has subscribed to dataset
        """
        statement = (
            self._build_query()
            .join(
                OrganisationDatasetSubscription,
                OrganisationDatasetSubscription.user_id == self._model.id,
            )
            .join(UserSettings, UserSettings.user_id == self._model.id)
            .where(
                OrganisationDatasetSubscription.dataset_id == dataset_id,
                UserSettings.mute_all_dataset_notifications.is_(False),
                self._model.is_active.is_(True),
            )
        )
        return self._fetch_all(statement)
