"""
Interface for email notifications to handle all the parameters
"""

import datetime
from typing import Any, Optional, Protocol


class INotifications(Protocol):
    """
    Sends notifications
    """

    def send_data_endpoint_validation_error_notification(
        self,
        contact_email: str,
        published_at: Optional[datetime.datetime],
        with_pti_violations: bool = False,
        **kwargs: Any,
    ):
        """Sends notification to Publisher that the Publication has validation errors
        Args:
            dataset_id: id (primary key) of the dataset model
            dataset_name: name assigned to the revision
            short_description: short description of the revision
            dataset_type: type of dataset: avl, fares or timetables
            published_at: date and time of publish
            comments: any comments on the revision
            feed_detail_link: link to the feed-detail or revision-publish page
            contact_email: email address of agent working on behalf of organisation
            with_pti_violations: boolean to indicate whether dataset has pti violations
        """

    def send_agent_data_endpoint_validation_error_notification(
        self,
        contact_email: str,
        published_at: Optional[datetime.datetime],
        with_pti_violations: bool = False,
        **kwargs: Any,
    ):
        """Sends notification to Agent that the Publication has validation errors
        Args:
            dataset_id: id (primary key) of the dataset model
            dataset_name: name assigned to the revision
            short_description: short description of the revision
            dataset_type: type of dataset: avl, fares or timetables
            published_at: date and time of publish
            operator_name: name of the operator that published the dataset
            comments: any comments on the revision
            feed_detail_link: link to the feed-detail or revision-publish page
            contact_email: email address of agent working on behalf of organisation
            with_pti_violations: boolean to indicate whether dataset has pti violations
        """

    def send_custom_email(
        self,
        template_id: str,
        subject: str,
        body: str,
        contact_email: str,
    ):
        """Sends a custom email.
        Args:
            template: template id for email
            subject: subject of email
            body: body of email
            contact_email: email address of datasets key contact
        """

    def send_data_endpoint_publish_notification(
        self,
        contact_email: str,
        published_at: Optional[datetime.datetime],
        with_pti_violations: bool,
        **kwargs: Any,
    ):
        """Send notification to operator for successful publish of dataset

        Args:
            contact_email (str): Email of the operator
            dataset_id (int): dataset id
            datast_name (str): dataset name
            short_description (str): description of the file
            published_at (Optional[datetime.datetime]): dataset published at
            comments (str): comments
            feed_detail_link (str): link of the timetable details
            with_pti_violations (bool): boolean to indicate whether dataset has pti violations
        """

    def send_agent_data_endpoint_publish_notification(
        self,
        contact_email: str,
        published_at: Optional[datetime.datetime],
        **kwargs: Any,
    ):
        """Send email notification to agent after successful publish of dataset

        Args:
            contact_email (str): Agent email id for the notification
            dataset_id (int): published dataset id
            dataset_name (str): published dataset name
            short_description (str): short description of the dataset
            published_at (Optional[datetime.datetime]): dataset published at
            comments (str): comments
            feed_detail_link (str): dataset details page link
            operator_name (str): operator name
            with_pti_violations (bool): boolean to indicate whether dataset has pti violations
        """

    def send_developer_data_endpoint_change_notification(
        self,
        contact_email: str,
        last_updated: Optional[datetime.datetime],
        **kwargs: Any,
    ):
        """Send email to dataset subscribers after successful publishing

        Args:
            contact_email (str): Email address of subscriber
            dataset_id (int): Published dataset id
            dataset_name (str): Published dataset name
            operator_name (str): Operator name
            last_updated (Optional[datetime.datetime]): Dataset last updated
        """
