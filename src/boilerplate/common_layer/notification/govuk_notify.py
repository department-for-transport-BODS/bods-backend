"""
GovUkNotifyEmail class to send emails via Gov UK portal
"""

from os import environ

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
        self._notification_client = NotificationsAPIClient(
            api_key=environ.get("GOV_NOTIFY_API_KEY", "-")
        )

    def _send_mail(
        self, feature: str, template_id: str, email: str, subject: str, **kwargs
    ) -> None:
        try:
            self._notification_client.send_email_notification(
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
