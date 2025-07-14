"""
Interface for email notifications to handle all the parameters
"""

import datetime
from typing import Protocol


class INotifications(Protocol):
    """
    Sends notifications
    """

    def send_data_endpoint_validation_error_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        dataset_type: int,
        published_at: datetime.datetime,
        comments: str,
        feed_detail_link: str,
        report_link: str,
        contact_email: str,
        with_pti_violations: bool = False,
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
        ...

    def send_agent_data_endpoint_validation_error_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        dataset_type: int,
        published_at: datetime.datetime,
        operator_name: str,
        comments: str,
        feed_detail_link: str,
        report_link: str,
        contact_email: str,
        with_pti_violations: bool = False,
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
        ...

    def send_custom_email(
        self,
        template: str,
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
        ...
