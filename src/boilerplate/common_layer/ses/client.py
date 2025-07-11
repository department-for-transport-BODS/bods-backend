"""
Email client for ETL Serverless lambdas
"""

from os import environ
from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError
from common_layer.exceptions.exception_email import SESEmailException
from structlog.stdlib import get_logger

if TYPE_CHECKING:
    from mypy_boto3_ses import SESClient

log = get_logger()


def send_email(
    emails: list[str],
    step: str,
    subject: str,
    content: str = "",
    is_html: bool = False,
) -> bool:
    """Send Email for serverless lambdas for ETL pipeline, AWS SES service will
    be utilised in order to send the emails

    Args:
        emails (list[str]): list of recepients email ids
        step (str): From which step did we triggered the email from
        subject (str): Subject content of the email
        content (str): Body content of the email can be html or text content
        is_html (bool): true is content is html content

    Returns:
        bool: Returns true always, because if failed to send an email, it should
        log the error but shouldn't raise an exception
    """
    try:
        ses_client: SESClient = boto3.client(  # type: ignore
            "ses", region_name=environ.get("AWS_REGION", "eu-west-2")
        )
        from_email = environ.get(
            "DEFAULT_FROM_EMAIL", "Bus Open Data Service <noreply@bods.com>"
        )

        content_type: str = "Text"
        if is_html:
            content_type: str = "Html"

        ses_client.send_email(
            Source=from_email,
            Destination={
                "ToAddresses": emails,
            },
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {  # type: ignore
                    content_type: {"Data": content, "Charset": "UTF-8"},
                },
            },
        )
    except ClientError:
        log.error(
            "botocore exceptions error ocurred while sending an email for ETL failure for step: ",
            step=step,
            exc_info=True,
        )
    except SESEmailException:
        log.error(
            "Error ocurred while sending an email for ETL failure for step: ",
            step=step,
            exc_info=True,
        )

    return True
