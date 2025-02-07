"""
Module to define the state machine functionality used by state runner
"""

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import structlog
from botocore.exceptions import BotoCoreError, ClientError
from structlog.stdlib import get_logger

from .models import (
    StateMachineInputS3Object,
    StateMachineS3Payload,
    StateMachineURLPayload,
)

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


class StateMachinesListError(Exception):
    """Custom exception for listing state machines failures."""


def clean_name(name: str) -> str:
    """
    Cleans a name to only allow 0-9, A-Z, a-z, - and _
    """
    cleaned = re.sub(r"[^a-zA-Z0-9\-_]", "", name)
    if cleaned != name:
        logger.warning(f"Name contained invalid characters: '{name}' -> '{cleaned}'")
    return cleaned


def create_event_payload(  # pylint: disable=too-many-arguments, too-many-positional-arguments
    data_source: str,
    object_key: str,
    revision_id: str,
    dataset_type: str,
    publish_data_revision: bool,
    overwrite_dataset: bool = False,
) -> StateMachineS3Payload | StateMachineURLPayload:
    """
    Creates event payload for state machine execution.
    """
    logger.info(
        "Creating event payload",
        data_source=data_source,
        key=object_key,
        revision_id=revision_id,
        dataset_type=dataset_type,
    )
    return (
        StateMachineS3Payload(
            inputDataSource=data_source,
            s3=StateMachineInputS3Object(object=object_key),
            datasetRevisionId=revision_id,
            datasetType=dataset_type,
            overwriteInputDataset=overwrite_dataset,
        )
        if data_source == "S3_FILE"
        else StateMachineURLPayload(
            inputDataSource=data_source,
            url=object_key,
            datasetRevisionId=revision_id,
            datasetType=dataset_type,
            publishDatasetRevision=publish_data_revision,
            overwriteInputDataset=overwrite_dataset,
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
        message = f"Could not find the matching state machine '{state_machine_name}'"
        logger.error(message)
        raise StateMachinesListError(message)
    except ClientError as e:
        message = f"Failed to list state machines in region '{client.meta.region_name}'"
        logger.error(message, exc_info=True)
        raise StateMachinesListError(message) from e
    except BotoCoreError as e:
        message = "A BotoCoreError occurred while listing state machines"
        logger.error(message, exc_info=True)
        raise StateMachinesListError(message) from e
    except Exception as e:
        message = "An unexpected error occurred"
        logger.error(message, exc_info=True)
        raise StateMachinesListError(message) from e


def generate_step_name(event: StateMachineS3Payload | StateMachineURLPayload) -> str:
    """
    Generate a unique step name
    """
    if isinstance(event, StateMachineURLPayload):
        object_key = Path(urlparse(event.url).path).name
    else:
        object_key = event.s3.object

    revision_id = event.datasetRevisionId
    key_names = object_key.split(".")
    key_name = "-".join(key_names[:-1])
    ext = key_names[-1]
    step_name = (
        f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{ext}-{revision_id}-{key_name}"
    )
    step_name = clean_name(step_name)[:80]
    logger.info("Generate step name", step_name=step_name)
    return step_name


def start_execution(
    client,
    state_machine_arn: str,
    event: StateMachineS3Payload | StateMachineURLPayload,
) -> str:
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
            input=json.dumps(event.model_dump()),
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
        message = (
            "Failed to start state machine execution for ARN '{state_machine_arn}'"
        )
        logger.error(message, exc_info=True)
        raise StateMachineExecutionError(message) from e
    except BotoCoreError as e:
        message = "A BotoCoreError occurred while starting the state machine execution"
        logger.error(message, exc_info=True)
        raise StateMachineExecutionError(message) from e
    except Exception as e:
        message = "An unexpected error occurred"
        logger.error(message, exc_info=True)
        raise StateMachineExecutionError(message) from e
