"""
Calculations in Execution Viewer
"""

from datetime import datetime

from mypy_boto3_stepfunctions import SFNClient
from mypy_boto3_stepfunctions.type_defs import HistoryEventTypeDef

from ..api_requests import get_execution_history
from ..models import ExecutionDetails, MapItemDuration, StepDuration


def analyze_step_durations(events: list[HistoryEventTypeDef]) -> list[StepDuration]:
    """Analyzes events to calculate step durations."""
    step_start_times: dict[str, datetime] = {}
    step_durations: list[StepDuration] = []

    for event in events:
        event_type: str = event["type"]
        timestamp: datetime = datetime.fromtimestamp(event["timestamp"].timestamp())

        if event_type.endswith("StateEntered"):
            state_entered_details = event.get("stateEnteredEventDetails", {})
            state_name: str = state_entered_details.get("name", "Unknown")
            step_start_times[state_name] = timestamp

        elif event_type.endswith("StateExited"):
            state_exited_details = event.get("stateExitedEventDetails", {})
            state_name: str = state_exited_details.get("name", "Unknown")
            if state_name in step_start_times:
                start_time = step_start_times[state_name]
                step_durations.append(
                    StepDuration(
                        name=state_name,
                        duration=timestamp - start_time,
                        start_time=start_time,
                        end_time=timestamp,
                    )
                )

    return step_durations


def analyze_map_durations(_events: list[HistoryEventTypeDef]) -> list[MapItemDuration]:
    """Analyzes events to calculate map state item durations."""
    # This is a placeholder for future implementation
    # Will extract durations for individual map state items
    return []


def enrich_execution_with_history(
    execution_details: ExecutionDetails, client: SFNClient
) -> ExecutionDetails:
    """Enriches execution details with history events data."""
    events = get_execution_history(client, execution_details.execution_arn)

    step_durations = analyze_step_durations(events)
    map_durations = analyze_map_durations(events)

    execution_details.steps = step_durations
    execution_details.map_items = map_durations

    return execution_details
