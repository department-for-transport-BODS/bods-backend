"""
API Requests
"""

from mypy_boto3_stepfunctions import SFNClient
from mypy_boto3_stepfunctions.type_defs import (
    DescribeExecutionOutputTypeDef,
    HistoryEventTypeDef,
)

from .helpers import calculate_duration
from .models import CloudWatchEventsExecutionDataDetails, ExecutionDetails


def get_execution_history(
    client: SFNClient, execution_arn: str
) -> list[HistoryEventTypeDef]:
    """Retrieves the history of events for a state machine execution."""
    paginator = client.get_paginator("get_execution_history")
    events: list[HistoryEventTypeDef] = []

    for page in paginator.paginate(executionArn=execution_arn):
        events.extend(page["events"])

    return events


def parse_execution_details(
    execution_details: DescribeExecutionOutputTypeDef,
) -> ExecutionDetails:
    """Parses raw execution details into a Pydantic model."""
    start_time = execution_details["startDate"]
    end_time = execution_details.get("stopDate")

    duration = calculate_duration(start_time, end_time)

    # Create input and output details
    input_details = CloudWatchEventsExecutionDataDetails(
        included=execution_details.get("inputDetails", {}).get("included", False),
        truncated=execution_details.get("inputDetails", {}).get("truncated", False),
    )

    output_details = CloudWatchEventsExecutionDataDetails(
        included=execution_details.get("outputDetails", {}).get("included", False),
        truncated=execution_details.get("outputDetails", {}).get("truncated", False),
    )

    return ExecutionDetails(
        execution_arn=execution_details["executionArn"],
        state_machine_arn=execution_details["stateMachineArn"],
        name=execution_details["name"],
        status=execution_details["status"],
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        # Add new fields
        input=execution_details.get("input", ""),
        input_details=input_details,
        output=execution_details.get("output", ""),
        output_details=output_details,
        map_run_arn=execution_details.get("mapRunArn", ""),
        error=execution_details.get("error", ""),
        cause=execution_details.get("cause", ""),
    )


def get_execution_details(
    client: SFNClient, state_machine_arn: str, execution_id: str
) -> ExecutionDetails:
    """Retrieves execution details for a state machine execution."""
    parts: list[str] = state_machine_arn.split(":")

    if len(parts) != 7 or parts[2] != "states" or "stateMachine" not in parts[5]:
        raise ValueError(f"Invalid state machine ARN: {state_machine_arn}")

    region: str = parts[3]
    account_id: str = parts[4]
    state_machine_name: str = parts[6]

    execution_arn: str = (
        f"arn:aws:states:{region}:{account_id}:execution:{state_machine_name}:{execution_id}"
    )

    execution_details_raw = client.describe_execution(executionArn=execution_arn)
    execution_details = parse_execution_details(execution_details_raw)

    return execution_details
