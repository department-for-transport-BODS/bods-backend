"""
Module to define the state machine functionality used by state runner
"""

import json
import random
import re
import string
from datetime import UTC, datetime

import structlog
from botocore.exceptions import BotoCoreError, ClientError
from structlog.stdlib import get_logger

from .models import Bucket, Detail, Event, Object

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ]
)

logger = get_logger()


class StateMachineExecutionError(Exception):
    """
    Custom exception for state machine execution failures.
    """

    pass


class StateMachinesListError(Exception):
    """Custom exception for listing state machines failures."""

    pass


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
            raise StateMachinesListError(
                f"Failed to list state machines in region '{client.meta.region_name}'"
            )
    except ClientError as e:
        logger.error(
            "Failed to list state machines in region",
            region=client.meta.region_name,
            state_machine_name=state_machine_name,
            error=str(e),
        )
        raise StateMachinesListError(
            f"Failed to list state machines in region '{client.meta.region_name}': {e}"
        ) from e
    except BotoCoreError as e:
        logger.error(
            "A BotoCoreError occurred while listing state machines",
            region=client.meta.region_name,
            state_machine_name=state_machine_name,
            error=str(e),
        )
        raise StateMachinesListError(
            f"A BotoCoreError occurred while listing state machines: {e}"
        ) from e
    except Exception as e:
        logger.error(
            "An unexpected error occurred",
            region=client.meta.region_name,
            state_machine_name=state_machine_name,
            error=str(e),
        )
        raise StateMachinesListError(f"An unexpected error occurred: {e}") from e


def generate_step_name(event: Event) -> str:
    """
    Generate a unique step name
    """
    object_key = event.detail.object.key
    revision_id = event.detail.datasetRevisionId
    unique_code = "".join(random.choices(string.ascii_letters, k=4))
    key_names = object_key.split(".")
    key_name = "-".join(key_names[:-1])
    ext = key_names[-1]
    step_name = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{ext}-{revision_id}-{key_name}-{unique_code}"
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

    except ClientError as e:
        logger.error(
            "Failed to start state machine execution for ARN",
            state_machine_arn=state_machine_arn,
            error=str(e),
        )
        raise StateMachineExecutionError(
            f"Failed to start state machine execution for ARN '{state_machine_arn}': {e}"
        ) from e
    except BotoCoreError as e:
        logger.error(
            "A BotoCoreError occurred while starting the state machine execution",
            state_machine_arn=state_machine_arn,
            error=str(e),
        )
        raise StateMachineExecutionError(
            f"A BotoCoreError occurred while starting the state machine execution: {e}"
        ) from e
    except Exception as e:
        logger.error(
            "An unexpected error occurred",
            state_machine_arn=state_machine_arn,
            error=str(e),
        )
        raise StateMachineExecutionError(f"An unexpected error occurred: {e}") from e
