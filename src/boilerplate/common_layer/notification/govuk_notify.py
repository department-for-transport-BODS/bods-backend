"""
GovUkNotifyEmail class to send emails via Gov UK portal
"""

import json
from os import environ
from typing import Any

import boto3
from botocore.exceptions import ClientError
from common_layer.exceptions.exception_email import GovUkEmailException
from common_layer.notification.base import NotificationBase
from notifications_python_client.notifications import NotificationsAPIClient
from structlog.stdlib import get_logger

log = get_logger()


class GovUKNotifyEmail(NotificationBase):
    """Gov UK implementation for email, inherits the notification base
    and implements send email method

    Args:
        NotificationBase (INotifications): Notification definitions
    """

    def __init__(self):
        super().__init__()

    def _send_mail(
        self,
        feature: str,
        template_id: str,
        email: str,
        **kwargs: dict[str, Any],
    ) -> None:
        try:
            dry_run = kwargs.get("dry_run", False)
            if dry_run:
                log.debug(
                    "Following args were recevied",
                    kwargs=kwargs,
                    email=email,
                    template_id=template_id,
                    feature=feature,
                )
            else:
                gov_uk_api_key = self._get_api_key()
                self._notification_client = NotificationsAPIClient(
                    api_key=gov_uk_api_key
                )
                self._notification_client.send_email_notification(  # type: ignore
                    email_address=email,
                    template_id=template_id,
                    personalisation=kwargs,
                )

        except GovUkEmailException:
            name = feature.lower()
            log.error(
                f"[notify_{name}] has encountered an exception while sending ",
                exc_info=True,
            )

    def _get_api_key(self) -> str:
        """
        Retrieves the value of a secret specified by its ARN.

        Parameters:
        - secret_arn (str): The ARN of the secret to retrieve.

        Returns:
        - str: The value of the retrieved secret.
        """
        try:
            session = boto3.session.Session()
            client = session.client(  # type: ignore
                service_name="secretsmanager",
                region_name=environ.get("AWS_REGION", "eu-west-2"),
            )
            response = client.get_secret_value(
                SecretId=environ.get("GOV_NOTIFY_API_ARN", "-")
            )
            log.info("The specified secret was successfully retrieved")
            return json.loads(response["SecretString"])
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":  # type: ignore
                log.error("The specified secret was not found")
            else:
                log.error(f'The error "{e}" occurred when retrieving the secret')
            raise
