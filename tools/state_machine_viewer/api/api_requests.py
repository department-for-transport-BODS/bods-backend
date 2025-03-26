"""
API Requests
"""

import boto3
from mypy_boto3_stepfunctions import SFNClient

from ..models import ExecutionDetails
from ..models.models_describe_executions import DescribeExecutionResponse
from ..models.models_execution_history import HistoryEvent
from ..models.models_map_runs import MapRunListItem


def get_step_functions_client(profile: str) -> SFNClient:
    """Creates a boto3 Step Functions client."""
    session = boto3.Session(profile_name=profile)
    client: SFNClient = session.client("stepfunctions")  # type: ignore
    return client


def get_map_runs_for_execution(
    client: SFNClient, execution_arn: str
) -> list[MapRunListItem]:
    """
    Get Map Run ARNs for a specific execution.
    """
    map_runs: list[MapRunListItem] = []

    paginator = client.get_paginator("list_map_runs")

    for page in paginator.paginate(executionArn=execution_arn):
        for map_run in page.get("mapRuns", []):
            map_runs.append(MapRunListItem.model_validate(map_run))

    return map_runs


def get_execution_history(client: SFNClient, execution_arn: str) -> list[HistoryEvent]:
    """Retrieves the history of events for a state machine execution."""
    paginator = client.get_paginator("get_execution_history")
    parsed_events: list[HistoryEvent] = []

    for page in paginator.paginate(executionArn=execution_arn):
        for event_data in page["events"]:
            parsed_events.append(HistoryEvent.model_validate(event_data))
    return parsed_events


def make_execution_arn(state_machine_arn: str, execution_id: str) -> str:
    """
    Make an ARN from the state machine arn
    """
    parts: list[str] = state_machine_arn.split(":")

    if len(parts) != 7 or parts[2] != "states" or "stateMachine" not in parts[5]:
        raise ValueError(f"Invalid state machine ARN: {state_machine_arn}")

    region: str = parts[3]
    account_id: str = parts[4]
    state_machine_name: str = parts[6]

    return f"arn:aws:states:{region}:{account_id}:execution:{state_machine_name}:{execution_id}"


def get_execution_details(
    client: SFNClient, state_machine_arn: str, execution_id: str
) -> ExecutionDetails:
    """Retrieves execution details for a state machine execution."""
    execution_arn = make_execution_arn(state_machine_arn, execution_id)
    execution_details = DescribeExecutionResponse.model_validate(
        client.describe_execution(executionArn=execution_arn)
    )
    history = get_execution_history(client, execution_arn)
    map_runs = get_map_runs_for_execution(client, execution_arn)
    return ExecutionDetails(
        describe=execution_details, history=history, map_runs=map_runs
    )
