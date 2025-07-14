import datetime
from abc import abstractmethod
from os import environ
from typing import Dict, Optional

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
    @property
    @abstractmethod
    def templates(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def _send_mail(self, template: str, email: str, subject: str, **kwargs):
        raise NotImplementedError

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def send_data_endpoint_validation_error_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        dataset_type: int,
        published_at: Optional[datetime.datetime],
        comments: str,
        feed_detail_link: str,
        report_link: str,
        contact_email: str,
        with_pti_violations: bool = False,
    ):
        feature = "OPERATOR_PUBLISH_ERROR"
        template_id = environ.get("GENERIC_TEMPLATE_ID", "-")
        logger.debug(
            f"[notify_{feature.lower()}] notifying organisation staff/admin dataset "
            f"Dataset<id={dataset_id}> has entered error state due to validation"
        )
        subject = "Error publishing data set"
        published_on = (
            "Not published"
            if published_at is None
            else localize_datetime_and_convert_to_string(published_at)
        )
        body = data_end_point_error_publishing(
            feed_name=dataset_name,
            feed_id=dataset_id,
            feed_short_description=short_description,
            published_time=published_on,
            comments=comments,
            link=feed_detail_link,
            report_link=report_link,
            dataset_type=dataset_type,
            user_type="organisation",
        )

        self._send_mail(
            feature,
            template_id,
            contact_email,
            subject=subject,
            body=body,
            feed_name=dataset_name,
            feed_id=dataset_id,
            feed_short_description=short_description,
            published_time=published_on,
            comments=comments,
            link=feed_detail_link,
            report_link=report_link,
            dataset_type=dataset_type,
            with_pti_violations=with_pti_violations,
        )

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def send_agent_data_endpoint_validation_error_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        dataset_type: int,
        published_at: Optional[datetime.datetime],
        operator_name: str,
        comments: str,
        feed_detail_link: str,
        report_link: str,
        contact_email: str,
        with_pti_violations: bool = False,
    ):
        feature = "AGENT_PUBLISH_ERROR"
        template_id = environ.get("GENERIC_TEMPLATE_ID", "-")
        logger.debug(
            f"[notify_{feature.lower()}] notifying organisation agent dataset "
            f"Dataset<id={dataset_id}> has entered error state due to validation"
        )
        subject = "Error publishing data set"

        if published_at is None:
            published_on = "Not published"
        else:
            published_on = localize_datetime_and_convert_to_string(published_at)

        body = data_end_point_error_publishing(
            feed_name=dataset_name,
            feed_id=dataset_id,
            feed_short_description=short_description,
            published_time=published_on,
            comments=comments,
            link=feed_detail_link,
            report_link=report_link,
            dataset_type=dataset_type,
            user_type="agent",
        )

        self._send_mail(
            feature,
            template_id,
            contact_email,
            subject=subject,
            body=body,
            feed_name=dataset_name,
            feed_id=dataset_id,
            organisation=operator_name,
            feed_short_description=short_description,
            published_time=published_on,
            comments=comments,
            link=feed_detail_link,
            report_link=report_link,
            dataset_type=dataset_type,
            with_pti_violations=with_pti_violations,
        )

    @validate_call
    def send_custom_email(
        self,
        template: str,
        subject: str,
        body: str,
        contact_email: str,
    ):
        logger.debug(f"sending custom email with template id: {template}")

        self._send_mail(
            template,
            contact_email,
            subject=subject,
            body=body,
        )
