"""
Helper Fuctions
"""

import json
from datetime import datetime, timedelta


def calculate_duration(start_time: datetime, end_time: datetime | None) -> timedelta:
    """Calculates duration between start and end times."""
    if end_time is None:
        end_time = datetime.now()
    return end_time - start_time


def format_duration(duration: timedelta) -> str:
    """Format timedelta into minutes and seconds."""
    total_seconds = int(duration.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}m {seconds}s"


def wrap_for_markdown(data: str) -> str:
    """
    Wrap data in appropriate markdown formatting.
    If it's valid JSON, pretty print it and wrap in a json code block.
    If it's text, quote each line with '> '.
    """
    if not data or data.strip() == "":
        return "No data available"

    try:
        # Parse JSON once
        parsed_json = json.loads(data)
        # Pretty print
        formatted_json = json.dumps(parsed_json, indent=2)
        # Wrap in code block
        return f"```json\n{formatted_json}\n```"
    except json.JSONDecodeError:
        # For text, split and quote each line
        lines = data.split("\n")
        quoted_lines = [f"> {line}" for line in lines]
        return "\n".join(quoted_lines)
