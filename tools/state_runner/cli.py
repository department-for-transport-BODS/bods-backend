"""
Tool allows to start an AWS Step Functions state machine execution with specified parameters.
It supports uploading a file to S3 before starting the state machine and provides logging for
the execution process.
"""

from typing import Optional

import typer
from structlog.stdlib import get_logger

from .s3_uploads import create_aws_session, upload_to_s3
from .state_machines import create_event_payload, get_state_machine_arn, start_execution

log = get_logger()
app = typer.Typer()


@app.command(name="start-state-machine")
def start_state_machine(  # pylint: disable=too-many-arguments, too-many-positional-arguments, too-many-locals
    bucket_name: str = typer.Option(
        "bodds-dev", "--bucket-name", help="Name of the S3 bucket"
    ),
    object_key: str = typer.Option(
        None,
        "--object-key",
        help="Key of the object in S3",
    ),
    url: str = typer.Option(
        None,
        "--url",
        help="File download URL",
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
    publish_data_revision: bool = typer.Option(
        False, "--publish-data-revision", help="Publish dataset revision"
    ),
    overwrite_dataset: bool = typer.Option(
        False, "--overwrite-dataset", help="Overwrite input dataset"
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
        log.info(
            "Starting state machine execution", state_machine_name=state_machine_name
        )

        if object_key and url:
            raise ValueError("Object key and url cannot be set at the same time")
        if url:
            data_source = "URL_DOWNLOAD"
        else:
            data_source = "S3_FILE"
        # Create AWS session
        session = create_aws_session(profile, region)

        # Upload file to s3
        if upload_file:
            s3_client = session.client("s3")  # type: ignore
            upload_to_s3(
                s3_client=s3_client,
                file_name=upload_file,
                bucket_name=bucket_name,
                object_name=object_key,
            )

        # Create event payload
        event = create_event_payload(
            data_source=data_source,
            object_key=object_key,
            url=url,
            revision_id=revision_id,
            dataset_type=dataset_type,
            publish_data_revision=publish_data_revision,
            overwrite_dataset=overwrite_dataset,
        )

        # Get statemachine ARN
        sfn_client = session.client("stepfunctions")  # type: ignore
        state_machine_arn = get_state_machine_arn(sfn_client, state_machine_name)

        # Start execution
        if state_machine_arn:
            console_link = start_execution(
                client=sfn_client, state_machine_arn=state_machine_arn, event=event
            )
            log.info(
                "AWS console link for running statemachine", console_link=console_link
            )
        log.info(
            "State machine execution started successfully!",
            state_machine_name=state_machine_name,
        )
    except Exception as e:
        log.error("An unexpected error occurred", error=str(e))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
