"""
SQL Alchemy BODs Database Client
"""

from contextlib import contextmanager
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Generator
from urllib.parse import quote_plus

import boto3
from pydantic import BaseModel, Field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from structlog.stdlib import get_logger

logger = get_logger()


class DatabaseBackend(str, Enum):
    """Supported database dialects."""

    POSTGRESQL = "postgresql"


class ProjectEnvironment(str, Enum):
    """Supported project environments."""

    LOCAL = "local"
    DEVELOPMENT = "dev"
    STAGING = "staging"
    TEST = "test"
    UAT = "uat"
    PRODUCTION = "prod"


class PostgresSettings(BaseSettings):
    """
    PostgreSQL database configuration settings.
    Automatically loads env vars
    """

    model_config = SettingsConfigDict(case_sensitive=False, extra="allow")

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
    POSTGRES_APPLICATION_NAME: str | None = Field(
        default=None,
        description="Application name for database connections",
        validation_alias="AWS_LAMBDA_FUNCTION_NAME",
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
        password = iam_token if self.use_iam_auth else self.POSTGRES_PASSWORD

        query_params: list[str] = []
        if self.ssl_mode:
            query_params.append(f"sslmode={self.ssl_mode}")
        if self.POSTGRES_APPLICATION_NAME:
            query_params.append(f"application_name={self.POSTGRES_APPLICATION_NAME}")

        query_string = "&".join(query_params) if query_params else None

        logger.info(
            "Constructing Connection URL",
            username=self.POSTGRES_USER,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
            ssl_mode=self.ssl_mode,
            application_name=self.POSTGRES_APPLICATION_NAME,
        )

        url = MultiHostUrl.build(
            scheme="postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=password,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
            query=query_string,
        )

        return str(url)


class DatabaseSettings(BaseModel):
    """Main database configuration settings."""

    model_config = SettingsConfigDict(case_sensitive=False)

    postgres: PostgresSettings


class SqlDB:
    """Manages database connections and sessions using SQLAlchemy."""

    def __init__(
        self,
        backend: DatabaseBackend = DatabaseBackend.POSTGRESQL,
        settings: DatabaseSettings | None = None,
    ) -> None:
        self.backend: DatabaseBackend = backend
        self._settings: DatabaseSettings = (
            settings if settings else DatabaseSettings(postgres=PostgresSettings())
        )
        self._engine: Engine | None = None
        self._session_factory: Callable[[], Session] | None = None
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
            if (
                self.backend == DatabaseBackend.POSTGRESQL
                and self._settings.postgres.use_iam_auth
            ):
                iam_token = self._generate_rds_iam_token()
                if not iam_token:
                    raise ValueError("Failed to generate IAM token")

            connection_url = self._settings.postgres.get_connection_url(iam_token)

            self._engine = create_engine(connection_url)

            if self.backend == DatabaseBackend.POSTGRESQL:
                self._token_expiration = datetime.now() + self._token_lifetime
            else:
                self._token_expiration = datetime.max

            logger.info(
                "Database engine initialized successfully",
                backend=self.backend,
            )
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
            if not self._settings.postgres.AWS_REGION:
                raise ValueError("AWS_REGION is required for IAM authentication")

            rds_client = boto3.session.Session().client(
                "rds", region_name=self._settings.postgres.AWS_REGION
            ) # type: ignore
            host = self._settings.postgres.POSTGRES_HOST
            user = self._settings.postgres.POSTGRES_USER
            port = self._settings.postgres.POSTGRES_PORT
            if host is None or user is None or port is None:
                logger.critical("Missing Postgres Variables", host=host)
                raise ValueError("Missing Values for generating IAM Token for RDS")
            token = rds_client.generate_db_auth_token(
                DBHostname=host,
                DBUsername=user,
                Port=port,
            )
            return quote_plus(token)
        except Exception:
            logger.exception("Failed to generate IAM auth token")
            raise
