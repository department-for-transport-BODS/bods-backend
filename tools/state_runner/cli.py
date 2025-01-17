"""
Database View Tool to search by revision id or service ID
"""

from typing import Optional

import structlog
import typer
from structlog.stdlib import get_logger

from .s3_uploads import create_aws_session, upload_to_s3
from .state_machines import create_event_payload, get_state_machine_arn, start_execution

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ]
)

logger = get_logger()

app = typer.Typer()


@app.command(name="start-state-machine")
def start_state_machine(
    bucket_name: str = typer.Option(
        "bodds-dev", "--bucket-name", help="Name of the S3 bucket"
    ),
    object_key: str = typer.Option(
        "coach-data/FLIX-FlixBus-N1710-Paris-London.xml",
        "--object-key",
        help="Key of the object in S3, when upload file option used file uploaded to the key given here",
    ),
    upload_file: str = typer.Option(
        None,
        "--upload-file",
        help="Source file to be uploaded to the s3 key given in object-key",
    ),
    revision_id: str = typer.Option(
        "3989", "--revision-id", help="Dataset revision ID"
    ),
    dataset_type: str = typer.Option(
        "timetables", "--dataset-type", help="Type of the dataset"
    ),
    state_machine_name: str = typer.Option(
        "bods-backend-dev-tt-sm",
        "--state-machine-name",
        help="ARN of the state machine",
    ),
    profile: Optional[str] = typer.Option(
        "boddsdev", "--profile", help="AWS profile to use"
    ),
    region: str = typer.Option("eu-west-2", "--region", help="AWS region"),
):
    """
    Start a state machine execution with the given parameters
    prerequisite:
    1. Set up aws profile and region
    2. login using command sso login --profile <profile-name>
    3. Now run this tool passing the parameters to start_state_machine
    """
    try:
        logger.info(
            "Starting state machine execution", state_machine_name=state_machine_name
        )

        # Create AWS session
        session = create_aws_session(profile, region)

        # Upload file to s3
        if upload_file:
            client = session.client("s3")
            upload_to_s3(
                s3_client=client,
                file_name=upload_file,
                bucket_name=bucket_name,
                object_name=object_key,
            )

        # Create event payload
        event = create_event_payload(
            bucket_name=bucket_name,
            object_key=object_key,
            revision_id=revision_id,
            dataset_type=dataset_type,
        )

        # Get statemachine ARN
        client = session.client("stepfunctions")
        state_machine_arn = get_state_machine_arn(client, state_machine_name)

        # Start execution
        if state_machine_arn:
            console_link = start_execution(
                client=client, state_machine_arn=state_machine_arn, event=event
            )
            logger.info(
                "AWS console link for running statemachine", console_link=console_link
            )
        logger.info(
            "State machine execution started successfully!",
            state_machine_name=state_machine_name,
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
