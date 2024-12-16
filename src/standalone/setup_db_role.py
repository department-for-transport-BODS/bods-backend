"""
Create RDS Proxy Role using the Admin Credentials
"""

import json
import logging
import os
import sys
from typing import Any, Callable

import boto3
import psycopg
import structlog
import urllib3
from botocore.exceptions import ClientError
from psycopg import sql
from psycopg.rows import dict_row
from structlog.processors import _json_fallback_handler
from structlog.stdlib import get_logger
from structlog.types import EventDict

logger = get_logger()
http = urllib3.PoolManager()


class AWSCloudWatchLogs:
    """
    Render a log line compatible with AWS CloudWatch Logs.
    AWS Cloudwatch Logs lets allows for two space separated items before the json log
    Which makes reading them in the logs easier

    """

    def __init__(
        self,
        callouts: list | None = None,
        serializer: Callable[..., str | bytes] = json.dumps,
        **dumps_kw: Any,
    ) -> None:
        if callouts is None:
            callouts = []
        self._callout_one_key = callouts[0] if len(callouts) > 0 else None
        self._callout_two_key = callouts[1] if len(callouts) > 1 else None
        dumps_kw.setdefault("default", _json_fallback_handler)
        self._dumps_kw = dumps_kw
        self._dumps = serializer

    def __call__(self, _, name: str, event_dict: EventDict) -> str | bytes:
        callout_one = (
            event_dict.get(self._callout_one_key, "")
            if self._callout_one_key
            else "none"
        )
        callout_two = (
            event_dict.get(self._callout_two_key, "")
            if self._callout_two_key
            else "none"
        )

        prefix = f'[{name.upper()}] "{callout_one}" "{callout_two}" '
        serialized = self._dumps(event_dict, **self._dumps_kw)

        if isinstance(serialized, str):
            return prefix + serialized
        if isinstance(serialized, bytes):
            return prefix.encode() + serialized
        raise TypeError(f"Unexpected type from serializer: {type(serialized)}")


_NOISY_LOG_SOURCES = (
    "boto",
    "boto3",
    "botocore",
    "urllib3",
    "s3transfer",
    "aws_xray_sdk",
)
_PROCESSORS = (
    structlog.stdlib.filter_by_level,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.UnicodeDecoder(),
    structlog.processors.CallsiteParameterAdder(
        {
            structlog.processors.CallsiteParameter.FUNC_NAME,
        }
    ),
    structlog.threadlocal.merge_threadlocal,
    AWSCloudWatchLogs(callouts=["event", "func_name"]),
)


def configure_logging():
    """
    Configure logging for the application.
    """

    # Structlog configuration
    structlog.configure(
        processors=list(_PROCESSORS),
        context_class=dict,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # reset the AWS-Lambda-supplied log handlers.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG,
        force=True,
    )
    for source in _NOISY_LOG_SOURCES:
        logging.getLogger(source).setLevel(logging.WARNING)


def generate_auth_token(host: str, port: str | int, username: str) -> str:
    """Generate an IAM authentication token for RDS"""
    client = boto3.client("rds")
    token = client.generate_db_auth_token(
        DBHostname=host,
        Port=int(port),
        DBUsername=username,
        Region=os.environ.get("AWS_REGION", "eu-west-2"),
    )
    logger.info("Generated Auth Token")
    return token


def send_cloudformation_response(
    event: dict[str, Any], context: Any, status: str, data: dict[str, Any] | None = None
) -> None:
    """
    Send response back to CloudFormation
    """
    response_body = {
        "Status": status,
        "Reason": "See CloudWatch logs for details",
        "PhysicalResourceId": context.log_stream_name,
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
        "Data": data or {},
    }

    logger.info("sending_cfn_response", **response_body)

    response_url = event["ResponseURL"]

    try:
        json_response_body = json.dumps(response_body)

        headers = {"content-type": "", "content-length": str(len(json_response_body))}

        response = http.request(
            "PUT",
            response_url,
            body=json_response_body.encode("utf-8"),
            headers=headers,
        )

        logger.info(
            "cfn_response_sent", status_code=response.status, response_url=response_url
        )

    except Exception as e:
        logger.error(
            "failed_to_send_cfn_response", error=str(e), response_url=response_url
        )
        raise


def get_secret(secret_name: str, client: Any | None = None) -> dict[str, Any]:
    """
    Get a single secret from AWS Secrets Manager.
    """
    if client is None:
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager")

    try:
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logger.error(
            "failed_to_get_secret",
            secret_name=secret_name,
            error=str(e),
        )
        raise

    if "SecretString" not in response:
        logger.error("no_secret_string_found", secret_name=secret_name)
        raise ValueError(f"No SecretString found in secret: {secret_name}")

    return json.loads(response["SecretString"])


def get_secrets() -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Get both admin and application user secrets from AWS Secrets Manager.

    """
    try:
        admin_secret_name = os.environ["SECRET_ARN"]
        app_secret_name = os.environ["APP_SECRET_ARN"]
    except KeyError as e:
        logger.error("missing_required_environment_variable", variable=str(e))
        raise

    logger.info(
        "retrieving_secrets",
        admin_secret_name=admin_secret_name,
        app_secret_name=app_secret_name,
    )

    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager")

    admin_secret = get_secret(admin_secret_name, client)
    app_secret = get_secret(app_secret_name, client)

    logger.info("successfully_retrieved_secrets")

    return admin_secret, app_secret


def create_db_connection(secret: dict[str, Any]) -> psycopg.Connection:
    """
    Create database connection with fallback authentication.
    First tries password auth, then falls back to IAM if that fails.

    Returns:
        psycopg.Connection: A valid database connection

    Raises:
        ValueError: If connection parameters are invalid
        psycopg.OperationalError: If both auth methods fail
    """
    host = os.environ.get("DB_HOST")
    port = os.environ.get("DB_PORT")
    dbname = os.environ.get("DB_NAME")
    username = secret.get("username")

    # Validate required parameters
    if not all([host, port, dbname, username]):
        raise ValueError("Missing required database connection parameters")

    base_params = {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": username,
        "row_factory": dict_row,
        "sslmode": "require",
    }

    # First attempt - password authentication
    logger.info(
        "attempting_db_password_auth",
        host=host,
        port=port,
        dbname=dbname,
        user=username,
        params=str({k: v for k, v in base_params.items() if k != "password"}),
    )

    try:
        conn_params = {**base_params, "password": secret["password"]}
        return psycopg.connect(**conn_params)
    except (psycopg.OperationalError, KeyError) as e:
        logger.info(
            "password_auth_failed_attempting_iam",
            error=str(e),
            host=host,
            port=port,
            dbname=dbname,
            user=username,
        )

        # Second attempt - IAM authentication
        if host is not None and port is not None and username is not None:

            try:
                auth_token = generate_auth_token(host, port, username)
                conn_params = {**base_params, "password": auth_token}
                conn = psycopg.connect(**conn_params)
                if conn is None:
                    raise ValueError("IAM connection returned None") from e
                return conn
            except (psycopg.OperationalError, ValueError) as iam_error:
                logger.error(
                    "iam_auth_failed",
                    error=str(iam_error),
                    host=host,
                    port=port,
                    dbname=dbname,
                    user=username,
                )
                raise
    raise ValueError("Could not establish DB Connection")


def check_role_existence(cur: psycopg.Cursor, role_name: str) -> bool:
    """
    Check if role exists
    """
    check_role_sql = sql.SQL(
        "SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname = {role}) as exists"
    )
    cur.execute(check_role_sql.format(role=sql.Literal(role_name)))

    result = cur.fetchone()
    if result is None:
        raise ValueError(
            "Database query returned no result when checking role existence"
        )

    # Access by column name since we're using dict_row
    role_exists = result["exists"]  # type: ignore

    logger.info("checked_role_existence", role_name=role_name, exists=role_exists)
    return role_exists


def execute_role_creation(
    cur: psycopg.Cursor, role_name: str, password: str, is_update: bool
) -> None:
    """Execute the SQL to create or update a role."""
    action = "updating" if is_update else "creating"
    logger.info(f"{action}_role", role_name=role_name)

    sql_template = "ALTER USER {role}" if is_update else "CREATE USER {role}"
    create_sql = sql.SQL(f"{sql_template} WITH PASSWORD {{password}}")

    cur.execute(
        create_sql.format(
            role=sql.Identifier(role_name), password=sql.Literal(password)
        )
    )


def configure_iam_auth(cur: psycopg.Cursor, role_name: str) -> None:
    """Configure IAM authentication for the role."""
    logger.info("configuring_iam_auth", role_name=role_name)
    iam_sql = sql.SQL("GRANT rds_iam TO {role}; ALTER USER {role} WITH LOGIN")
    cur.execute(iam_sql.format(role=sql.Identifier(role_name)))


def validate_app_secret(app_secret: dict[str, Any]) -> None:
    """Validate the app secret contains required fields."""
    if "password" not in app_secret:
        raise ValueError("App secret missing required 'password' field")


def handle_database_error(
    e: psycopg.Error, role_name: str, conn: psycopg.Connection
) -> None:
    """Handle PostgreSQL-specific errors."""
    error_msg = f"Database error: {str(e)}"
    logger.error(
        "failed_to_create_or_update_role",
        role_name=role_name,
        error=error_msg,
        error_type=type(e).__name__,
        pgcode=getattr(e, "pgcode", None),
        pgerror=getattr(e, "pgerror", None),
    )
    conn.rollback()
    raise RuntimeError(error_msg) from e


def handle_generic_error(
    e: Exception, role_name: str, conn: psycopg.Connection
) -> None:
    """Handle any other unexpected errors."""
    error_msg = f"Unexpected error: {str(e)}"
    logger.error(
        "Failed to Create or update role",
        role_name=role_name,
        error=error_msg,
        error_type=type(e).__name__,
        error_details=repr(e),
    )
    conn.rollback()
    raise RuntimeError(error_msg) from e


def create_or_update_role(
    conn: psycopg.Connection, app_secret: dict[str, Any], role_name: str = "bodds_rw"
) -> None:
    """Main function to create or update a database role."""
    logger.info("creating_or_updating_role", role_name=role_name)

    try:
        validate_app_secret(app_secret)

        with conn.cursor() as cur:
            # Check if role exists and create/update accordingly
            role_exists = check_role_existence(cur, role_name)
            execute_role_creation(cur, role_name, app_secret["password"], role_exists)

            # If using RDS Proxy Don't use IAM Auth
            # configure_iam_auth(cur, role_name)

        conn.commit()
        logger.info("role_created_or_updated_successfully", role_name=role_name)

    except psycopg.Error as e:
        handle_database_error(e, role_name, conn)
    except Exception as e:
        handle_generic_error(e, role_name, conn)


def grant_role_permissions(
    conn: psycopg.Connection, role_name: str = "bodds_rw"
) -> None:
    """
    Grants necessary permissions to the database role.
    """
    logger.info("granting_role_permissions", role_name=role_name)

    statements = [
        # Database privileges
        sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {db} TO {role}").format(
            db=sql.Identifier(os.environ["DB_NAME"]), role=sql.Identifier(role_name)
        ),
        # Schema privileges
        sql.SQL(
            """
            GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {role};
            GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {role};
            GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO {role};
        """
        ).format(role=sql.Identifier(role_name)),
        # Default privileges
        sql.SQL(
            """
            ALTER DEFAULT PRIVILEGES IN SCHEMA public 
                GRANT ALL PRIVILEGES ON TABLES TO {role};
            ALTER DEFAULT PRIVILEGES IN SCHEMA public 
                GRANT ALL PRIVILEGES ON SEQUENCES TO {role};
            ALTER DEFAULT PRIVILEGES IN SCHEMA public 
                GRANT ALL PRIVILEGES ON FUNCTIONS TO {role};
        """
        ).format(role=sql.Identifier(role_name)),
        # Schema usage
        sql.SQL(
            """
            GRANT USAGE ON SCHEMA pg_catalog TO {role};
            GRANT USAGE ON SCHEMA information_schema TO {role};
        """
        ).format(role=sql.Identifier(role_name)),
        # Catalog access
        sql.SQL(
            """
            GRANT SELECT ON pg_catalog.pg_namespace TO {role};
            GRANT SELECT ON pg_catalog.pg_class TO {role};
            GRANT SELECT ON pg_catalog.pg_roles TO {role};
            GRANT SELECT ON pg_catalog.pg_user TO {role};
            GRANT SELECT ON pg_catalog.pg_tables TO {role};
            GRANT SELECT ON pg_catalog.pg_views TO {role};
            
            GRANT SELECT ON ALL TABLES IN SCHEMA information_schema TO {role};
        """
        ).format(role=sql.Identifier(role_name)),
    ]

    try:
        with conn.cursor() as cur:
            for statement in statements:
                try:
                    cur.execute(statement)
                except Exception as e:
                    logger.error("failed_to_execute_permission_statement", error=str(e))
                    raise

        conn.commit()
        logger.info("permissions_granted", role_name=role_name)

    except Exception as e:
        logger.error("failed_to_grant_permissions", error=str(e))
        conn.rollback()
        raise


def setup_database_role(
    conn: psycopg.Connection, app_secret: dict[str, Any], role_name: str = "bodds_rw"
) -> None:
    """
    Main function to set up the database role with all necessary permissions.
    """
    try:
        logger.info("starting_database_role_setup", role_name=role_name)

        if not isinstance(app_secret, dict):
            raise ValueError(f"Invalid app_secret type: {type(app_secret)}")

        if "password" not in app_secret:
            raise ValueError("app_secret missing required 'password' field")

        create_or_update_role(conn, app_secret, role_name)
        grant_role_permissions(conn, role_name)

        logger.info(
            "database_role_setup_completed", role_name=role_name, setup_status="success"
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(
            "database_role_setup_failed",
            role_name=role_name,
            error=error_msg,
            error_type=type(e).__name__,
            setup_status="failed",
        )
        raise RuntimeError(f"Database role setup failed: {error_msg}") from e


def enable_postgis_extension(conn: psycopg.Connection) -> None:
    """
    Enable PostGIS extension on the database.
    If enabling fails, log the error but continue execution.
    """
    logger.info("Enabling PostGIS Extension for Geometry types")

    try:
        with conn.cursor() as cur:
            # Check if PostGIS is already enabled
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 
                    FROM pg_extension 
                    WHERE extname = 'postgis'
                ) as exists;
            """
            )
            result = cur.fetchone()

            if result and not result["exists"]:  # type: ignore
                # Enable PostGIS if not already enabled
                cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
                logger.info("postgis_extension_enabled")
            else:
                logger.info("postgis_extension_already_enabled")

        conn.commit()

    except psycopg.Error as e:
        logger.error(
            "Failed to enable PostGIS extension",
            error=str(e),
            error_type=type(e).__name__,
            pgcode=getattr(e, "pgcode", None),
            pgerror=getattr(e, "pgerror", None),
        )
        conn.rollback()
    except Exception as e:
        logger.error(
            "Unexpected error enabling PostGIS",
            error=str(e),
            error_type=type(e).__name__,
        )
        conn.rollback()


def validate_environment() -> None:
    """
    Validate all required environment variables are present
    """
    required_vars = [
        "SECRET_ARN",
        "APP_SECRET_ARN",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "AWS_REGION",
    ]

    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error("missing_environment_variables", missing_vars=missing_vars)
        raise ValueError(msg)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Main Lambda handler with proper connection management
    """
    configure_logging()
    validate_environment()
    logger.info("Starting DB Role Lambda", input_data=event)
    conn = None

    try:
        # Only process Create and Update events
        if event["RequestType"] in ["Create", "Update"]:
            admin_secret, app_secret = get_secrets()
            conn = create_db_connection(admin_secret)
            setup_database_role(conn, app_secret)

            logger.info("Completed Role Setup")
            enable_postgis_extension(conn)

            send_cloudformation_response(event, context, "SUCCESS")
            return {"statusCode": 200, "body": "Role setup completed successfully"}

        # For Delete events, just send success response
        if event["RequestType"] == "Delete":
            logger.info("processing_delete_event")
            send_cloudformation_response(event, context, "SUCCESS")
            return {"statusCode": 200, "body": "Nothing to delete"}

        msg = "Unsupported request type"
        logger.error(
            "Unsupported Cloudformation Request Type", request_type=event["RequestType"]
        )
        send_cloudformation_response(event, context, "FAILED", {"Error": msg})
        return {"statusCode": 400, "body": msg}

    except Exception as e:
        error_message = str(e)
        logger.error("setup_failed", error=error_message)
        send_cloudformation_response(event, context, "FAILED", {"Error": error_message})
        raise

    finally:
        if conn is not None:
            try:
                conn.close()
                logger.info("database_connection_closed")
            except Exception as e:
                logger.error("error_closing_connection", error=str(e))
