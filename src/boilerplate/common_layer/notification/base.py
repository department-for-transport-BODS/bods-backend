"""
Notification base class for writting all the emails implementations which can
be sent from the server less
"""

import datetime
from abc import abstractmethod
from os import environ
from typing import Any, Dict, Optional

from common_layer.notification.emails import data_end_point_error_publishing
from common_layer.notification.local_time import localize_datetime_and_convert_to_string
from pydantic import ConfigDict, validate_call
from structlog.stdlib import get_logger

logger = get_logger()

TEMPLATE_LOOKUP: Dict[str, str] = {
    "OPERATOR_PUBLISH_ERROR": "notifications/data_end_point_error_publishing.txt",
    "AGENT_PUBLISH_ERROR": "notifications/data_end_point_error_publishing_agent.txt",
}


class NotificationBase:
    """
    Notification base class with methods implementation
    """

    @abstractmethod
    def _send_mail(
        self,
        feature: str,
        template_id: str,
        email: str,
        **kwargs: Any,
    ) -> None:
        """Send email method, must be implemented by the inheriting class

        Args:
            feature (str): Name of the email
            template_id (str): id of the template in case
            email (str): email id of receiver
            subject (str): subject of the email

        Raises:
            NotImplementedError: Exception if not implemented
        """
        raise NotImplementedError

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def send_data_endpoint_validation_error_notification(
        self,
        contact_email: str,
        published_at: Optional[datetime.datetime],
        with_pti_violations: bool = False,
        **kwargs: Any,
    ) -> None:
        """Sends notification to Publisher that the Publication has validation errors
        Args:
            feed_id: id (primary key) of the dataset model
            dataset_name: name assigned to the revision
            feed_short_description: short description of the revision
            dataset_type: type of dataset: avl, fares or timetables
            published_at: date and time of publish
            comments: any comments on the revision
            feed_detail_link: link to the feed-detail or revision-publish page
            contact_email: email address of agent working on behalf of organisation
            with_pti_violations: boolean to indicate whether dataset has pti violations
        """
        feature = "OPERATOR_PUBLISH_ERROR"
        template_id = environ.get("GENERIC_TEMPLATE_ID", "-")
        logger.debug(
            f"[notify_{feature.lower()}] notifying organisation staff/admin dataset "
            f"Dataset<id={kwargs['feed_id']}> has entered error state due to validation"
        )
        subject = "Error publishing data set"
        published_on: str = (
            "Not published"
            if published_at is None
            else localize_datetime_and_convert_to_string(published_at)
        )
        body = data_end_point_error_publishing(
            published_time=published_on, user_type="organisation", kwargs=kwargs
        )

        kwargs["body"] = body
        kwargs["subject"] = subject
        kwargs["with_pti_violations"] = with_pti_violations
        kwargs["published_on"] = published_on

        self._send_mail(feature, template_id, contact_email, **kwargs)

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def send_agent_data_endpoint_validation_error_notification(
        self,
        contact_email: str,
        published_at: Optional[datetime.datetime],
        with_pti_violations: bool = False,
        **kwargs: Any,
    ) -> None:
        """Sends notification to Agent that the Publication has validation errors
        Args:
            feed_id: id (primary key) of the dataset model
            dataset_name: name assigned to the revision
            feed_short_description: short description of the revision
            dataset_type: type of dataset: avl, fares or timetables
            published_at: date and time of publish
            operator_name: name of the operator that published the dataset
            comments: any comments on the revision
            feed_detail_link: link to the feed-detail or revision-publish page
            contact_email: email address of agent working on behalf of organisation
            with_pti_violations: boolean to indicate whether dataset has pti violations
        """
        feature = "AGENT_PUBLISH_ERROR"
        template_id = environ.get("GENERIC_TEMPLATE_ID", "-")
        logger.debug(
            f"[notify_{feature.lower()}] notifying organisation agent dataset "
            f"Dataset<id={kwargs['feed_id']}> has entered error state due to validation"
        )
        kwargs["subject"] = "Error publishing data set"

        published_on = (
            "Not published"
            if published_at is None
            else localize_datetime_and_convert_to_string(published_at)
        )

        kwargs["body"] = data_end_point_error_publishing(
            published_time=published_on, user_type="agent", kwargs=kwargs
        )
        kwargs["with_pti_violations"] = with_pti_violations
        kwargs["published_on"] = published_on

        self._send_mail(feature, template_id, contact_email, **kwargs)

    @validate_call
    def send_custom_email(
        self,
        template_id: str,
        subject: str,
        body: str,
        contact_email: str,
    ):
        """Method for sending the custom emails

        Args:
            template_id (str): Template id
            subject (str): Subject of email
            body (str): body content of email
            contact_email (str): Receivers email id
        """
        logger.debug(f"sending custom email with template id: {template_id}")

        kwargs: dict[str, Any] = {"subject": subject, "body": body}

        self._send_mail("custom_email", template_id, contact_email, **kwargs)
