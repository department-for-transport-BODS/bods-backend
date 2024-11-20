"""
SQL Alchemy BODs Database Client
"""

from contextlib import contextmanager
from datetime import datetime, timedelta
from enum import Enum
from logging import getLogger
from typing import Any, Generator
from urllib.parse import quote_plus

import boto3
from pydantic import Field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, sessionmaker

logger = getLogger()


class ProjectEnvironment(str, Enum):
    """Supported project environments."""

    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class PostgresSettings(BaseSettings):
    """
    PostgreSQL database configuration settings.
    Automatically loads env vars
    """

    model_config = SettingsConfigDict(case_sensitive=False)

    POSTGRES_HOST: str | None = Field(default=None, description="Database host address")
    POSTGRES_DB: str | None = Field(default=None, description="Database name")
    POSTGRES_USER: str | None = Field(default=None, description="Database username")
    POSTGRES_PORT: int | None = Field(
        default=None, description="Database port", gt=0, le=65535
    )
    POSTGRES_PASSWORD: str | None = Field(
        default=None,
        description="Database password (only used in local environment)",
    )
    PROJECT_ENV: ProjectEnvironment = Field(
        default=ProjectEnvironment.LOCAL, description="Project environment"
    )
    AWS_REGION: str | None = Field(
        default=None, description="AWS region for IAM authentication"
    )

    @property
    def use_iam_auth(self) -> bool:
        """Determine if IAM authentication should be used."""
        return self.PROJECT_ENV != ProjectEnvironment.LOCAL

    @property
    def ssl_mode(self) -> str:
        """Get SSL mode based on environment."""
        return "require" if self.use_iam_auth else "disable"

    def get_connection_url(self, iam_token: str | None = None) -> str:
        """
        Generate PostgreSQL connection URL.

        """
        if self.use_iam_auth and not iam_token:
            raise ValueError("IAM token required for non-local environment")

        url = MultiHostUrl.build(
            scheme="postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
            query=f"sslmode={self.ssl_mode}" if self.ssl_mode else None,
        )

        return str(url)


class BodsDB:
    """Manages database connections and sessions using SQLAlchemy."""

    def __init__(self, settings: PostgresSettings | None = None) -> None:
        self._settings: PostgresSettings = settings if settings else PostgresSettings()
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

    def _initialize_database_classes(self) -> None:
        """Initializes SQLAlchemy mapped classes."""
        base = automap_base()
        base.prepare(autoload_with=self.engine)
        self._classes = base.classes
        logger.info("Database classes initialized")

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

    def _initialize_engine(self) -> None:
        """Initializes SQLAlchemy engine with connection details."""
        try:
            iam_token = None
            if self._settings.use_iam_auth:
                iam_token = self._generate_rds_iam_token()
                if not iam_token:
                    raise ValueError("Failed to generate IAM token")

            connection_url = self._settings.get_connection_url(iam_token)

            self._engine = create_engine(connection_url)
            self._token_expiration = datetime.now() + self._token_lifetime
            logger.info("Database engine initialized successfully")
        except Exception:
            logger.exception("Failed to initialize SQLAlchemy engine")
            raise

    def _should_refresh_token(self) -> bool:
        """Determines if IAM token needs refresh."""
        if not self._engine or not self._token_expiration:
            return True
        return datetime.now() >= (
            self._token_expiration - self._refresh_token_threshold
        )

    def _generate_rds_iam_token(self) -> str:
        """
        Generates AWS RDS IAM authentication token.
        """
        try:
            if not self._settings.AWS_REGION:
                raise ValueError("AWS_REGION is required for IAM authentication")

            rds_client = boto3.session.Session().client(
                "rds", region_name=self._settings.AWS_REGION
            )

            token = rds_client.generate_db_auth_token(
                DBHostname=self._settings.POSTGRES_HOST,
                DBUsername=self._settings.POSTGRES_USER,
                Port=self._settings.POSTGRES_PORT,
            )
            return quote_plus(token)
        except Exception:
            logger.exception("Failed to generate IAM auth token")
            raise
