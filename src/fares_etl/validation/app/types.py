"""
Shared Types for Fares Validation
"""

import json
from pathlib import Path
from typing import IO, Any, AnyStr

from pydantic import BaseModel

XMLFile = AnyStr | IO[Any]
JSONFile = IO[Any]


class Rule(BaseModel):
    """
    XML Schema Rule
    """

    test: str


class Observation(BaseModel):
    """
    XML Schema Observation
    """

    details: str
    category: str
    context: str
    rules: list[Rule]


class Header(BaseModel):
    """
    XML Header
    """

    namespaces: dict[str, str]


class Schema(BaseModel):
    """
    XML Validation Schema
    """

    observations: list[Observation]
    header: Header

    @classmethod
    def from_path(cls, path: Path):
        """
        Load schema from path
        """
        with path.open("r") as f:
            d = json.load(f)
            return cls(**d)


class XMLViolationDetail:
    """
    Detail about XML Validation Error
    """

    violation_line = 0

    def __init__(
        self,
        violation_line: str | int | None = None,
        violation_message: str = "",
    ):
        self.violation_line = str(violation_line) if violation_line else None
        self.violation_message = violation_message
        self.violation_detail = []

        self.violation_detail = [
            self.violation_line,
            self.violation_message,
        ]

    def __list__(self):
        return self.violation_detail
