"""
Create the Tables in the DB
"""

import os
from typing import Any

import urllib3
from common_layer.cfn import cloudformation_response
from common_layer.database.client import SqlDB
from common_layer.database.create_tables import create_db_tables
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

logger = get_logger()
http = urllib3.PoolManager()


@cloudformation_response()
def lambda_handler(_event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """
    Run Create Tables on DB
    """
    configure_logging()
    try:
        logger.info("Starting table creation")

        environment = os.environ.get("PROJECT_ENV", "local")
        if environment not in ["standalone", "local"]:
            msg = f"Table creation not allowed in {environment} environment"
            logger.warning(msg, environment=environment)
            return {"message": msg, "data": {"Status": "Skipped"}}

        db = SqlDB()
        create_db_tables(db)

        return {
            "message": "Database tables created successfully",
            "data": {"Status": "Tables Created"},
        }

    except Exception as e:
        logger.error("Failed to create tables", error=str(e))
        raise
