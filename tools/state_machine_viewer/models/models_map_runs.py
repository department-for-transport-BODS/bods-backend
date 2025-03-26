"""
Maps Runs
"""

from datetime import datetime, timedelta
from functools import cached_property

from pydantic import BaseModel, computed_field

from tools.state_machine_viewer.helpers import calculate_duration


class MapRunListItem(BaseModel):
    """
    Map Run List
    """

    executionArn: str
    mapRunArn: str
    stateMachineArn: str
    startDate: datetime
    stopDate: datetime

    @computed_field
    @cached_property
    def duration(self) -> timedelta:
        """Calculates the duration of the execution."""
        return calculate_duration(self.startDate, self.stopDate)
