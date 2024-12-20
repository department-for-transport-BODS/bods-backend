"""
Shared Pydantic Models for the CLI
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestConfig:
    """Configuration for the test environment"""

    txc_paths: list[Path]
    db_host: str = "localhost"
    db_name: str = "bods-local"
    db_user: str = "bods-local"
    db_password: str = "bods-local"
    db_port: int = 5432
    parallel: bool = False
    max_workers: int = 10
    create_tables: bool = False
    task_id: int | None = None
    file_attributes_id: int | None = None
    revision_id: int | None = None
