"""
Module to provide common functionality for TxC tools
"""

from enum import Enum
import structlog

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ]
)

log = structlog.stdlib.get_logger()


class ReportMode(str, Enum):
    """Type of file processing"""

    SIZE = "size"
    TAG = "tag"
    TXC = "txc"
