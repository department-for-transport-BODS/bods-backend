"""
API functions to fetch Map execution details from AWS Step Functions
"""

from datetime import datetime, timedelta

from mypy_boto3_stepfunctions import SFNClient
from mypy_boto3_stepfunctions.type_defs import (
    ExecutionListItemTypeDef,
    HistoryEventTypeDef,
    MapRunItemCountsTypeDef,
)
from structlog.stdlib import get_logger

from .execution_viewer.map_info_models import (
    MapExecution,
    MapExecutionItem,
    MapRunStats,
)
from .helpers import calculate_duration
from .models import ExecutionDetails

log = get_logger()


def get_execution_history(
    client: SFNClient, execution_arn: str
) -> list[HistoryEventTypeDef]:
    """Retrieves the history of events for a state machine execution."""
    paginator = client.get_paginator("get_execution_history")
    events: list[HistoryEventTypeDef] = []

    for page in paginator.paginate(executionArn=execution_arn):
        events.extend(page["events"])

    return events


def find_map_state_name(client: SFNClient, execution_arn: str, map_run_arn: str) -> str:
    """Find the Map state name that produced the given Map Run."""
    events = get_execution_history(client, execution_arn)

    # Find the MapRunStarted event for this map_run_arn
    map_run_event = next(
        (
            event
            for event in events
            if "mapRunStartedEventDetails" in event
            and event.get("mapRunStartedEventDetails", {}).get("mapRunArn")
            == map_run_arn
            and event.get("type") == "MapRunStarted"
        ),
        None,
    )

    if not map_run_event:
        return "Unknown Map State"

    # Get the previous event ID
    prev_event_id = map_run_event.get("previousEventId")
    if prev_event_id is None:
        return "Unknown Map State"

    # Find the state entered event
    prev_event = next(
        (
            event
            for event in events
            if event.get("id") == prev_event_id and "stateEnteredEventDetails" in event
        ),
        None,
    )

    if prev_event:
        return prev_event.get("stateEnteredEventDetails", {}).get(
            "name", "Unknown Map State"
        )

    return "Unknown Map State"


def parse_map_item_counts(item_counts: MapRunItemCountsTypeDef) -> MapRunStats:
    """Parse the MapRunItemCounts into MapRunStats."""
    return MapRunStats(
        total_items=item_counts.get("total", 0),
        pending_items=item_counts.get("pending", 0),
        running_items=item_counts.get("running", 0),
        succeeded_items=item_counts.get("succeeded", 0),
        failed_items=item_counts.get("failed", 0),
        timed_out_items=item_counts.get("timedOut", 0),
        aborted_items=item_counts.get("aborted", 0),
        results_written=item_counts.get("resultsWritten", 0),
        failures_not_redrivable=item_counts.get("failuresNotRedrivable", 0),
        pending_redrive=item_counts.get("pendingRedrive", 0),
        avg_duration=timedelta(),  # Initialize with zero duration
        min_duration=timedelta(),
        max_duration=timedelta(),
        total_duration=timedelta(),
    )


def get_map_runs_for_execution(client: SFNClient, execution_arn: str) -> list[str]:
    """
    Get Map Run ARNs for a specific execution.
    """
    map_run_arns: list[str] = []

    paginator = client.get_paginator("list_map_runs")

    for page in paginator.paginate(executionArn=execution_arn):
        for map_run in page.get("mapRuns", []):
            map_run_arn = map_run.get("mapRunArn")
            if map_run_arn:
                map_run_arns.append(map_run_arn)

    return map_run_arns


def get_map_execution_details(
    client: SFNClient, map_run_arn: str
) -> MapExecution | None:
    """
    Fetch complete details about a Map execution, including all its child executions.
    """
    map_run = client.describe_map_run(mapRunArn=map_run_arn)

    execution_arn = map_run.get("executionArn", "")

    state_name = find_map_state_name(client, execution_arn, map_run_arn)

    map_execution = MapExecution(
        map_run_arn=map_run_arn,
        execution_arn=execution_arn,
        state_machine_arn=map_run.get("stateMachineArn", ""),
        state_name=state_name,
        status=map_run.get("status", "UNKNOWN"),
        start_time=map_run.get("startDate", datetime.now()),
        end_time=map_run.get("stopDate"),
        duration=calculate_duration(map_run.get("startDate"), map_run.get("stopDate")),
        max_concurrency=map_run.get("maxConcurrency", 0),
        tolerated_failure_percentage=map_run.get("toleratedFailurePercentage", 0.0),
        tolerated_failure_count=map_run.get("toleratedFailureCount", 0),
        redrive_count=map_run.get("redriveCount", 0),
        redrive_date=map_run.get("redriveDate"),
        stats=parse_map_item_counts(map_run.get("itemCounts", {})),
        executions=[],
    )

    paginator = client.get_paginator("list_executions")
    executions: list[ExecutionListItemTypeDef] = []

    for page in paginator.paginate(mapRunArn=map_run_arn):
        executions.extend(page.get("executions", []))

    for execution in executions:
        execution_arn = execution.get("executionArn", "")

        execution_details = client.describe_execution(executionArn=execution_arn)

        execution_name = execution_arn.split(":")[-1]

        item = MapExecutionItem(
            execution_arn=execution_arn,
            execution_name=execution_name,
            index=int(execution.get("itemCount", 0)),
            status=execution_details.get("status", "UNKNOWN"),
            start_time=execution_details.get("startDate", datetime.now()),
            end_time=execution_details.get("stopDate"),
            duration=calculate_duration(
                execution_details.get("startDate"),
                execution_details.get("stopDate"),
            ),
            input=execution_details.get("input", ""),
            output=execution_details.get("output", ""),
            error=execution_details.get("error", ""),
            cause=execution_details.get("cause", ""),
            redrive_count=execution_details.get("redriveCount", 0),
            redrive_date=execution_details.get("redriveDate"),
        )

        map_execution.executions.append(item)

    map_execution.update_stats_from_executions()

    return map_execution


def get_all_map_executions(
    client: SFNClient, execution_details: ExecutionDetails
) -> list[MapExecution]:
    """
    Get all Map executions for a Step Functions execution.

    """
    map_executions: list[MapExecution] = []

    map_run_arns = get_map_runs_for_execution(client, execution_details.execution_arn)

    for map_run_arn in map_run_arns:
        map_execution = get_map_execution_details(client, map_run_arn)
        if map_execution:
            map_executions.append(map_execution)

    return map_executions
