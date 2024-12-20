"""
Shared Pydantic Models for the CLI
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class DbConfig:
    """
    Database Config Vars
    """

    host: str
    port: int
    database: str
    user: str
    password: str


@dataclass
class TestConfig:
    """Configuration for the test environment"""

    txc_paths: list[Path]
    db_config: DbConfig
    parallel: bool = False
    max_workers: int = 10
    create_tables: bool = False
    task_id: int | None = None
    file_attributes_id: int | None = None
    revision_id: int | None = None
