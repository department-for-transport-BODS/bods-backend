"""
Runs send email validation check
"""

from datetime import datetime

import typer
from common_layer.notification import get_notifications
from structlog.stdlib import get_logger

from tools.common.db_tools import dotenv_loader

app = typer.Typer()
log = get_logger()


@app.command(name="send-email")
def main(
    dataset_id: int = typer.Option(12304, "--dataset_id", help="The dataset id"),
    dataset_name: str = typer.Option(
        "Test dataset", "--dataset_name", help="The dataset name for the revision"
    ),
    dataset_link: str = typer.Option(
        "https://data.bus-data.dft.gov.uk/timetable/dataset/12345/",
        "--dataset_link",
        help="The dataset link for the revision",
    ),
    short_description: str = typer.Option(
        "Short description about the dataset",
        "--short_description",
        help="The short description about the dataset",
    ),
    dataset_type: int = typer.Option(
        1, "--dataset_type", help="The type of the dataset"
    ),
    published_at: datetime = typer.Option(
        "2025-01-31T10:00:00", "--published_at", help="Dataset published date"
    ),
    comments: str = typer.Option(
        "comments for the dataset",
        "--comments",
        help="The short description about the dataset",
    ),
    feed_detail_link: str = typer.Option(
        "feed details link", "--feed_detail_link", help="Link for the feed details"
    ),
    contact_email: str = typer.Option(
        "test@bus-data.dft.gov.uk", "--contact_email", help="Receivers email address"
    ),
    with_pti_violations: bool = typer.Option(
        False,
        "--with_pti_violations",
        help="boolean to indicate whether dataset has pti violations",
    ),
    dry_run: bool = typer.Option(
        True, "--dry-run", help="Dry run without calling the send email"
    ),
    use_dotenv: bool = typer.Option(
        True,
        "--use-dotenv",
        help="Load env configurations from .env file",
    ),
):
    """Send email method for testing the sending email logic without actually sending an email"""

    if use_dotenv:
        dotenv_loader()

    notification = get_notifications()
    notification.send_data_endpoint_validation_error_notification(
        contact_email,
        published_at,
        with_pti_violations=with_pti_violations,
        feed_id=dataset_id,
        feed_name=dataset_name,
        feed_short_description=short_description,
        dataset_type=dataset_type,
        comments=comments,
        feed_detail_link=feed_detail_link,
        report_link=dataset_link,
        dry_run=dry_run,
    )

    notification.send_agent_data_endpoint_validation_error_notification(
        contact_email,
        published_at,
        with_pti_violations=with_pti_violations,
        feed_id=dataset_id,
        feed_name=dataset_name,
        feed_short_description=short_description,
        dataset_type=dataset_type,
        comments=comments,
        feed_detail_link=feed_detail_link,
        report_link=dataset_link,
        dry_run=dry_run,
        operator_name="operator-name",
    )


if __name__ == "__main__":
    app()
