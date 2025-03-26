"""
Execution History
"""

from datetime import datetime
from typing import Annotated, Any, Type, TypeGuard, TypeVar, cast

from pydantic import BaseModel, Field, model_validator

T = TypeVar("T", bound="HistoryEvent")


def is_str_dict(obj: Any) -> TypeGuard[dict[str, Any]]:
    """
    Check if a dict with str keys
    """
    return isinstance(obj, dict) and all(isinstance(k, str) for k in obj)  # type: ignore


class InputOutputDetails(BaseModel):
    """Details about whether input or output was truncated"""

    truncated: Annotated[
        bool, Field(description="Indicates if the data was truncated")
    ] = False


class TaskCredentials(BaseModel):
    """Task credentials for execution"""

    roleArn: Annotated[
        str | None, Field(description="The ARN of the IAM role that the task uses")
    ] = None


class EventDetails(BaseModel):
    """Unified model for all event details with type discriminator"""

    type: Annotated[
        str, Field(description="The event type (matches the parent event's type)")
    ]

    # Input/Output fields
    input: Annotated[str | None, Field(description="The JSON data input")] = None
    inputDetails: Annotated[
        InputOutputDetails | None,
        Field(description="Contains details about input truncation"),
    ] = None
    output: Annotated[str | None, Field(description="The JSON data output")] = None
    outputDetails: Annotated[
        InputOutputDetails | None,
        Field(description="Contains details about output truncation"),
    ] = None

    # State related fields
    name: Annotated[
        str | None, Field(description="The name of the state or iteration")
    ] = None
    assignedVariables: Annotated[
        dict[str, str] | None,
        Field(description="Variables assigned during state execution"),
    ] = None
    assignedVariablesDetails: Annotated[
        InputOutputDetails | None,
        Field(description="Contains details about assigned variables truncation"),
    ] = None

    # Error/cause fields
    error: Annotated[str | None, Field(description="The error code")] = None
    cause: Annotated[
        str | None, Field(description="A more detailed explanation of the cause")
    ] = None

    # Resource fields
    resource: Annotated[
        str | None, Field(description="The resource ARN or identifier")
    ] = None
    resourceType: Annotated[
        str | None, Field(description="The type of the resource")
    ] = None
    roleArn: Annotated[str | None, Field(description="The ARN of the IAM role")] = None

    # Lambda specific
    taskCredentials: Annotated[
        TaskCredentials | None, Field(description="The task credentials")
    ] = None
    timeoutInSeconds: Annotated[
        int | None, Field(description="Timeout for the task or activity")
    ] = None
    heartbeatInSeconds: Annotated[
        int | None, Field(description="The maximum time between heartbeats")
    ] = None

    # Map/iteration related
    index: Annotated[int | None, Field(description="The index of the iteration")] = None
    length: Annotated[
        int | None, Field(description="The size of the array being processed")
    ] = None
    mapRunArn: Annotated[str | None, Field(description="The ARN of the map run")] = None
    redriveCount: Annotated[
        int | None,
        Field(description="The number of times execution or map run has been redriven"),
    ] = None

    # Parameters
    parameters: Annotated[
        str | None, Field(description="The parameters for the task")
    ] = None
    region: Annotated[str | None, Field(description="The AWS region")] = None

    # For worker info
    workerName: Annotated[str | None, Field(description="The name of the worker")] = (
        None
    )

    # For state machine related fields
    stateMachineAliasArn: Annotated[
        str | None, Field(description="The ARN of the state machine alias")
    ] = None
    stateMachineVersionArn: Annotated[
        str | None, Field(description="The ARN of the state machine version")
    ] = None

    # Other fields
    location: Annotated[
        str | None, Field(description="The location where an evaluation failed")
    ] = None
    state: Annotated[
        str | None, Field(description="The state where an evaluation failed")
    ] = None


class HistoryEvent(BaseModel):
    """A simplified event in the execution history of a Step Function"""

    id: Annotated[int, Field(description="The id of the event")]
    timestamp: Annotated[
        datetime, Field(description="The date and time the event occurred")
    ]
    type: Annotated[str, Field(description="The type of the event")]
    previousEventId: Annotated[
        int | None, Field(description="The id of the previous event")
    ] = None
    details: Annotated[
        EventDetails | None,
        Field(description="Unified event details extracted from type-specific fields"),
    ] = None

    @model_validator(mode="before")
    @classmethod
    def extract_details(cls: Type[T], data: dict[str, Any] | Any) -> dict[str, Any]:
        """Extract the event details into a unified details field"""
        if not is_str_dict(data):
            return data

        model_data: dict[str, Any] = data.copy()

        event_type: str = data.get("type", "")
        if not event_type:
            return model_data

        # Check for all potential event detail keys
        detail_keys = [k for k in data.keys() if k.endswith("EventDetails")]

        # If we found any event details
        if detail_keys:
            details_key = detail_keys[0]  # Take the first one if multiple exist
            details_data = cast(dict[str, Any], data.get(details_key, {}))

            # Add the event type to the details
            details_data["type"] = event_type
            model_data["details"] = details_data

            # Remove the original details field
            if details_key in model_data:
                model_data.pop(details_key)

        return model_data
