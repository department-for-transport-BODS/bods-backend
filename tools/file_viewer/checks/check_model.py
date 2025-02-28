"""
Check Models Shared
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel
from textual.containers import Container


class CheckResult(BaseModel):
    """
    BaseModel for Checks with result key
    """

    result: bool = False


CheckInputData = TypeVar("CheckInputData")
CheckOutputData = TypeVar("CheckOutputData", bound=CheckResult)


@dataclass
class Check(Generic[CheckInputData, CheckOutputData]):
    """
    Set up checks
    """

    name: str
    check_func: Callable[[CheckInputData], CheckOutputData]
    detail_func: Callable[[CheckOutputData], Container]
    result: bool | None = None
