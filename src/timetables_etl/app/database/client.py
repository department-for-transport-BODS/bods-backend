"""
SQL Alchemy BODs Database Client
"""

from contextlib import contextmanager
from datetime import datetime, timedelta
from logging import getLogger
from os import environ
from typing import Any, Generator
from urllib.parse import quote_plus

import boto3
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, sessionmaker

logger = getLogger()


class BodsDB:
    """Manages database connections and sessions using SQLAlchemy."""

    def __init__(self) -> None:
        self._engine: Engine | None = None
        self._session_factory = None
        self._classes = None
        self._token_expiration: datetime | None = None
        self._refresh_token_threshold = timedelta(seconds=30)
        self._token_lifetime = timedelta(minutes=15)

    @property
    def engine(self) -> Engine:
        """Returns existing engine or creates new one if token expired."""
        if self._should_refresh_token():
            self._initialize_engine()
        if not self._engine:
            raise RuntimeError("Database Engine initialization failed")
        return self._engine

    @property
    def classes(self) -> Any:
        """Returns mapped database classes."""
        if self._classes is None:
            self._initialize_database_classes()
        return self._classes

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provides transactional scope around operations."""
        if not self._session_factory:
            self._session_factory = sessionmaker(bind=self.engine)

        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _should_refresh_token(self) -> bool:
        """Determines if IAM token needs refresh."""
        if not self._engine or not self._token_expiration:
            return True
        return datetime.now() >= (
            self._token_expiration - self._refresh_token_threshold
        )

    def _get_session_factory(self) -> sessionmaker:
        """Returns session factory, creating if needed."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine)
        return self._session_factory

    def _initialize_engine(self) -> None:
        """Initializes SQLAlchemy engine with connection details."""
        connection_details = self._get_connection_details()

        try:
            self._engine = create_engine(
                self._generate_connection_string(**connection_details)
            )
            self._token_expiration = datetime.now() + self._token_lifetime
            logger.info("Database engine initialized successfully")
        except Exception:
            logger.exception("Failed to initialize SQLAlchemy engine")
            raise

    def _initialize_database_classes(self) -> None:
        """Initializes SQLAlchemy mapped classes."""
        base = automap_base()
        base.prepare(autoload_with=self.engine)
        self._classes = base.classes
        logger.info("Database classes initialized")

    def _get_connection_details(self) -> dict[str, str]:
        """Retrieves database connection details from environment."""
        required_vars = {
            "host": "POSTGRES_HOST",
            "dbname": "POSTGRES_DB",
            "user": "POSTGRES_USER",
            "port": "POSTGRES_PORT",
        }

        connection_details: dict[str, str] = {}

        for key, env_var in required_vars.items():
            value = environ.get(env_var)
            if value is None:
                raise ValueError(f"Missing required environment variable: {env_var}")
            connection_details[key] = value

        host = connection_details["host"]
        port = connection_details["port"]
        user = connection_details["user"]

        if environ.get("PROJECT_ENV") != "local":
            token = self._generate_rds_iam_token(host, port, user)
            if token is None:
                raise ValueError("Failed to generate IAM token")
            connection_details["password"] = token
            connection_details["sslmode"] = "require"
        else:
            password = environ.get("POSTGRES_PASSWORD", "password")
            connection_details["password"] = password
            connection_details["sslmode"] = "disable"

        return connection_details

    def _generate_connection_string(self, **kwargs) -> str:
        """Generates PostgreSQL connection string."""
        auth = f"{kwargs['user']}:{kwargs['password']}@" if kwargs.get("user") else ""

        params = {
            k: v
            for k, v in kwargs.items()
            if k not in ["host", "port", "user", "password", "dbname"] and v
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        base_url = f"postgresql+psycopg2://{auth}{kwargs['host']}"

        if kwargs.get("port"):
            base_url += f":{kwargs['port']}"

        if kwargs.get("dbname"):
            base_url += f"/{kwargs['dbname']}"

        if query_string:
            base_url += f"?{query_string}"

        return base_url

    def _generate_rds_iam_token(self, host: str, port: str, username: str) -> str:
        """Generates AWS RDS IAM authentication token."""
        try:
            rds_client = boto3.session.Session().client(
                "rds", region_name=environ.get("AWS_REGION")
            )
            token = rds_client.generate_db_auth_token(
                DBHostname=host, DBUsername=username, Port=port
            )
            return quote_plus(token)
        except Exception:
            logger.exception("Failed to generate IAM auth token")
            raise
