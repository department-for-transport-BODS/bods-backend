"""
Configuration for db-viewer tool
"""

from dataclasses import dataclass


@dataclass
class DbConfig:
    """
    Configuration for DB connection
    """

    host: str
    port: int
    database: str
    user: str
    password: str
