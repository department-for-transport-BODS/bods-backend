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
    )

    try:
        conn_params = {**base_params, "password": secret["password"]}
        conn = psycopg.connect(**conn_params)
        if conn is None:
            raise ValueError("Connection returned None")
        return conn
    except (psycopg.OperationalError, KeyError, ValueError) as e:
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


def setup_database_role(
    conn: psycopg.Connection, app_secret: dict[str, Any], role_name: str = "bodds_rw"
) -> None:
    """
    Set up application database role with password and IAM authentication.

    Args:
        conn: Database connection to use for setup
        app_secret: Secret containing the application user credentials
        role_name: Name of the role to create/update, defaults to "bodds_rw"

    Raises:
        Exception: If any database operations fail
    """
    logger.info("setting_up_database_role", role_name=role_name)

    statements = [
        # Create role if it doesn't exist with password
        {
            "name": "create_role",
            "sql": f"""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{role_name}') THEN
                            CREATE USER {role_name} WITH PASSWORD %s;
                        ELSE
                            ALTER USER {role_name} WITH PASSWORD %s;
                        END IF;
                    END
                    $$;
                """,
            "params": (app_secret["password"], app_secret["password"]),
        },
        # Configure authentication methods
        {
            "name": "configure_auth",
            "sql": f"""
                GRANT rds_iam TO {role_name};
                ALTER USER {role_name} WITH LOGIN;
            """,
            "params": None,  # No parameters needed anymore
        },
        # Grant database privileges
        {
            "name": "grant_db_privileges",
            "sql": f"GRANT ALL PRIVILEGES ON DATABASE {os.environ['DB_NAME']} TO {role_name};",
            "params": None,
        },
        # Grant schema privileges
        {
            "name": "grant_schema_privileges",
            "sql": f"""
                DO $$
                BEGIN
                    -- Grant privileges on public schema
                    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {role_name};
                    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {role_name};
                    GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO {role_name};
                    
                    -- Set default privileges for future objects
                    ALTER DEFAULT PRIVILEGES IN SCHEMA public 
                        GRANT ALL PRIVILEGES ON TABLES TO {role_name};
                    ALTER DEFAULT PRIVILEGES IN SCHEMA public 
                        GRANT ALL PRIVILEGES ON SEQUENCES TO {role_name};
                    ALTER DEFAULT PRIVILEGES IN SCHEMA public 
                        GRANT ALL PRIVILEGES ON FUNCTIONS TO {role_name};

                    -- Grant minimal required catalog access
                    GRANT USAGE ON SCHEMA pg_catalog TO {role_name};
                    GRANT USAGE ON SCHEMA information_schema TO {role_name};
                    
                    -- Grant access to specific catalog views
                    GRANT SELECT ON pg_catalog.pg_namespace TO {role_name};
                    GRANT SELECT ON pg_catalog.pg_class TO {role_name};
                    GRANT SELECT ON pg_catalog.pg_roles TO {role_name};
                    GRANT SELECT ON pg_catalog.pg_user TO {role_name};
                    GRANT SELECT ON pg_catalog.pg_tables TO {role_name};
                    GRANT SELECT ON pg_catalog.pg_views TO {role_name};
                    
                    -- Grant access to information_schema views
                    GRANT SELECT ON ALL TABLES IN SCHEMA information_schema TO {role_name};
                END
                $$;
            """,
            "params": None,  # No parameters needed anymore since we're using f-strings
        },
    ]

    try:
        with conn.cursor() as cur:
            for statement in statements:
                try:
                    logger.info(
                        "executing_statement",
                        statement_name=statement["name"],
                    )
                    cur.execute(statement["sql"], statement.get("params", None))
                    logger.info(
                        "executed_statement",
                        statement_name=statement["name"],
                        role_name=role_name,
                    )
                except Exception as e:
                    logger.error(
                        "failed_to_execute_statement",
                        statement_name=statement["name"],
                        error=str(e),
                    )
                    raise

        conn.commit()
        logger.info("committed_changes", role_name=role_name)

    except Exception as e:
        logger.error("failed_to_setup_database_role", error=str(e))
        conn.rollback()
        raise


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Main Lambda handler
    """
    configure_logging()
    logger.info("Starting DB Role Lambda", input_data=event)

    try:
        # Only process Create and Update events
        if event["RequestType"] in ["Create", "Update"]:
            admin_secret, app_secret = get_secrets()

            conn = create_db_connection(admin_secret)
            if not conn:
                raise ValueError("Failed to create database connection")

            setup_database_role(conn, app_secret)
            conn.close()

            logger.info("setup_completed_successfully")
            send_cloudformation_response(event, context, "SUCCESS")
            return {"statusCode": 200, "body": "Role setup completed successfully"}

        # For Delete events, just send success response
        if event["RequestType"] == "Delete":
            logger.info("processing_delete_event")
            send_cloudformation_response(event, context, "SUCCESS")
            return {"statusCode": 200, "body": "Nothing to delete"}

        msg = "Unsupported request type"
        logger.error("unsupported_request_type", request_type=event["RequestType"])
        send_cloudformation_response(event, context, "FAILED", {"Error": msg})
        return {"statusCode": 400, "body": msg}

    except Exception as e:
        error_message = str(e)
        logger.error("setup_failed", error=error_message)
        # Make sure to send the failure response before raising
        send_cloudformation_response(event, context, "FAILED", {"Error": error_message})
        raise  # Re-raise the exception after sending the response
