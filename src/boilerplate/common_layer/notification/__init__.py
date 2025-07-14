from common_layer.notification.govuk_notify import (
    GovUKNotifyEmail,
)
from common_layer.notification.interface import INotifications


def get_notifications() -> INotifications:
    """
    Returns adapter implementing INotification interface using NOTIFIER setting
    """
    return GovUKNotifyEmail()
