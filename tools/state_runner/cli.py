"""
Database View Tool to search by revision id or service ID
"""

import json
import random
import re
import string
from datetime import UTC, datetime
from typing import Optional

import boto3
import structlog
import typer
from pydantic import BaseModel
from structlog.stdlib import get_logger

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ]
)

logger = get_logger()

app = typer.Typer()


class Bucket(BaseModel):
    """
    Class to hold information about S3 bucket.
    """

    name: str


class Object(BaseModel):
    """
    Class to hold information about S3 object key.
    """

    key: str


class Detail(BaseModel):
    """
    Class to hold information about state machine payload details.
    """

    bucket: Bucket
    object: Object
    datasetRevisionId: str
    datasetType: str


class Event(BaseModel):
    """
    Class to hold information about state machine payload events.
    """

    detail: Detail


def create_aws_session(profile: Optional[str], region: str) -> boto3.Session:
    """
    Creates AWS session with optional profile
    """
    try:
        return (
            boto3.Session(profile_name=profile, region_name=region)
            if profile
            else (boto3.Session(region_name=region))
        )

    except Exception as e:
        logger.error(f"Failed to create AWS session: {e}")
        raise typer.Exit(1)


def clean_name(name: str) -> str:
    """
    Cleans a name to only allow 0-9, A-Z, a-z, - and _
    """
    cleaned = re.sub(r"[^a-zA-Z0-9\-_]", "", name)
    if cleaned != name:
        logger.warning(f"Name contained invalid characters: '{name}' -> '{cleaned}'")
    return cleaned


def create_event_payload(
    bucket_name: str, object_key: str, revision_id: str, dataset_type: str
) -> Event:
    """
    Creates event payload for state machine execution.
    """
    logger.info(
        "Creating event payload",
        bucket=bucket_name,
        key=object_key,
        revision_id=revision_id,
        dataset_type=dataset_type,
    )
    return Event(
        detail=Detail(
            bucket=Bucket(name=bucket_name),
            object=Object(key=object_key),
            datasetRevisionId=revision_id,
            datasetType=dataset_type,
        )
    )


def get_state_machine_arn(client, state_machine_name) -> str:
    """
    Retrieve the ARN of a state machine by its name
    """
    try:
        logger.info(
            "Getting statemachine ARN from statemachine name", name=state_machine_name
        )
        client_response = client.list_state_machines()
        for state_machine in client_response["stateMachines"]:
            if state_machine["name"] == state_machine_name:
                logger.info("Found state machine", details=state_machine)
                return state_machine["stateMachineArn"]
        else:
            logger.error(
                "Could not find the matching state machine", name=state_machine_name
            )
    except Exception as err:
        logger.error(
            "Could not retrieve state machine ARN",
            name=state_machine_name,
            error=str(err),
        )
        raise typer.Exit(1)


def generate_step_name(event: Event) -> str:
    """
    Generate a unique step name
    """
    object_key = event.detail.object.key
    revision_id = event.detail.datasetRevisionId
    unique_code = "".join(random.choices(string.ascii_letters, k=4))
    key_names = object_key.split(".")
    key_name = '-'.join(key_names[:-1])
    ext = key_names[-1]
    step_name = (
        f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{ext}-{revision_id}-{key_name}-{unique_code}"
    )
    step_name = clean_name(step_name)[:80]
    logger.info("Generate step name", step_name=step_name)
    return step_name


def start_execution(client, state_machine_arn: str, event: Event) -> str:
    """
    Execute statemachine with payload
    """
    try:
        logger.info(
            "Starting statemachine execution", state_machine_arn=state_machine_arn
        )
        client_response = client.start_execution(
            stateMachineArn=state_machine_arn,
            name=generate_step_name(event),
            input=json.dumps([event.model_dump()]),
        )
        logger.info(
            "Statemachine execution started successfully!", arn=state_machine_arn
        )
        region = client.meta.region_name
        exec_arn = client_response["executionArn"]
        return (
            f"https://{region}.console.aws.amazon.com/states/home?"
            f"region={region}#/executions/details/{exec_arn}"
        )

    except Exception as e:
        logger.error("Error starting state machine execution", error=str(e))
        raise typer.Exit(1)


@app.command(name="start-state-machine")
def start_state_machine(
    bucket_name: str = typer.Option(
        "bodds-dev", "--bucket-name", help="Name of the S3 bucket"
    ),
    object_key: str = typer.Option(
        "coach-data/xml/FLIX-FlixBus-UK020-London-Birmingham.xml",
        "--object-key",
        help="Key of the object in S3",
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
        logger.info("Starting state machine execution",
                    state_machine_name=state_machine_name)
        # Create event payload
        event = create_event_payload(
            bucket_name=bucket_name,
            object_key=object_key,
            revision_id=revision_id,
            dataset_type=dataset_type,
        )

        # Create AWS session
        session = create_aws_session(profile, region)
        client = session.client("stepfunctions")

        # Get statemachine ARN
        state_machine_arn = get_state_machine_arn(client, state_machine_name)

        # Start execution
        if state_machine_arn:
            console_link = start_execution(
                client=client, state_machine_arn=state_machine_arn, event=event
            )
            logger.info(
                "AWS console link for running statemachine", console_link=console_link
            )
        logger.info("State machine execution started successfully!", state_machine_name=state_machine_name)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
