"""
Display Models
"""

from datetime import datetime, timedelta

from pydantic import BaseModel


class StepDuration(BaseModel):
    """Step execution duration information."""

    name: str
    duration: timedelta
    start_time: datetime
    end_time: datetime
