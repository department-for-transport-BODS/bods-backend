import boto3
import datetime
import pandas as pd
import time
import urllib.parse
from json import loads
from logger import logger
from os import environ
from pydantic import BaseModel
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, select


db_instance = None
token_expiration_time = None

class LambdaEvent:
    """
    Class to handle request for the lambda function
    Properties:
    db: Database connection object with session management and caching
    """

    def __init__(self, lambda_event):
        self._lambda_event = lambda_event

    def __str__(self) -> str:
        return f"Lambda event occured"

    @property
    def db(self):
        """
        Property to access the database connection object with token expiration handling,
        reusing the global database engine while creating a new session per invocation
        """
        global db_instance
        global token_expiration_time

        current_time = time.time()

        if db_instance is None or token_expiration_time is None or current_time >= token_expiration_time:
            logger.debug("Initialising new BodsDB instance with refreshed IAM authentication token")
            db_instance, token_expiration_time = self._initialise_db()
        else:
            logger.debug("Re-using cached BodsDB instance as still valid")

        return db_instance

    def _initialise_db(self):
        """
        Initialises the BodsDB instance and sets the token expiration time.
        """
        db = BodsDB()
        token_expiration = time.time() + (15 * 60) - 30 # AWS default token expiration is 15 minutes. Settings to time less 30s as safeguard
        logger.debug(f"New token expiration set for {datetime.datetime.utcfromtimestamp(token_expiration)}")
        return db, token_expiration


class BodsDB:
    """
    Class to handle the connection to the BODS database using either RDS Proxy IAM
    authentication, or user/password authentication. The class provides properties
    to access the database session and classes
    """

    def __init__(self):
        self._classes = None
        self._engine = None
        self._session = None

    @property
    def session(self):
        """
        Property to access the database session. A new session is created for each invocation.
        This session will use the globally cached engine
        """
        if self._engine is None:
            self._initialise_engine()
        
        if self._session is None:
            SessionMaker = sessionmaker(bind=self._engine)
            self._session = SessionMaker()

        return self._session

    @property
    def classes(self):
        """
        Property to access the database classes
        """
        if self._classes is None:
            self._initialise_database_classes()
        return self._classes

    def _initialise_engine(self):
        """
        Initialises the SQLAlchemy engine. This is cached globally and reused across invocations
        """
        connection_details = self._get_connection_details()
        logger.info("Connecting to DB")
        
        try:
            start_init_op = time.time()
            self._engine = create_engine(
                self._generate_connection_string(**connection_details)
            )
            end_init_op = time.time()
            logger.info(f"DB initialisation operation took {end_init_op-start_init_op:.2f} seconds")
        except Exception as e:
            logger.error(f"Failed to initialise SQLAlchemy engine: {e}")
            raise

    def _initialise_database_classes(self):
        """
        Initialises the SQLAlchemy base (metadata/classes). This is done once per Lambda 
        execution environment
        """
        if self._engine is None:
            self._initialise_engine()

        self._sqlalchemy_base = automap_base()
        logger.info("Preparing SQLAlchemy base")
        self._sqlalchemy_base.prepare(autoload_with=self._engine)
        self._classes = self._sqlalchemy_base.classes
        logger.info("Set DB classes")


    def _get_connection_details(self):
        """
        Method to get the connection details for the database from the environment variables
        """
        connection_details = {}
        connection_details["host"] = environ.get("POSTGRES_HOST")
        connection_details["dbname"] = environ.get("POSTGRES_DB")
        connection_details["user"] = environ.get("POSTGRES_USER")
        connection_details["port"] = environ.get("POSTGRES_PORT")
        try:
            if environ.get("PROJECT_ENV") != "local":
                logger.debug("Getting DB IAM authentication token")
                start_auth_op = time.time()
                connection_details["password"] = self._generate_rds_iam_auth_token(
                    connection_details["host"],
                    connection_details["port"],
                    connection_details["user"],
                )
                end_auth_op = time.time()
                logger.debug(f"DB IAM authentication token generation took {end_auth_op-start_auth_op:.2f} seconds")
                connection_details["sslmode"] = "require"
            else:
                logger.debug(
                    "Running in local environment, using DB password obtained from environment variables"
                )
                connection_details["password"] = environ.get("POSTGRES_PASSWORD", "password")
                logger.debug("Got DB password")
                connection_details["sslmode"] = "disable"

            for key, value in connection_details.items():
                if value is None:
                    logger.error(f"Missing connection details value: {key}")
                    raise ValueError
            return connection_details
        except Exception as e:
            logger.error("Failed to get connection details for database")
            raise e

    def _generate_connection_string(self, **kwargs) -> str:
        """
        Generates an AWS RDS IAM authentication token for a given RDS instance.

        Args:
            **kwargs (any): A dictionary of key/value pairs that correspond to the expected values below

        Returns:
            str: The generated connection string from parsed key/value pairs
        """
        user_password = ""
        if kwargs.get("user"):
            user_password += kwargs.get("user")
            if kwargs.get("password"):
                user_password += ":" + kwargs.get("password")
            user_password += "@"

        # Construct other parts
        other_parts = ""
        for key, value in kwargs.items():
            if key not in ["host", "port", "user", "password", "dbname"] and value:
                other_parts += f"{key}={value}&"

        # Construct the final connection string
        connection_string = (
            f"postgresql+psycopg2://{user_password}{kwargs.get('host', '')}"
        )
        if kwargs.get("port"):
            connection_string += f":{kwargs.get('port')}"
        connection_string += f"/{kwargs.get('dbname', '')}"
        if other_parts:
            connection_string += f"?{other_parts[:-1]}"

        return connection_string

    def _generate_rds_iam_auth_token(self, host, port, username) -> str:
        """
        Generates an AWS RDS IAM authentication token for a given RDS instance.

        Args:
            hostname (str): The endpoint of the RDS instance.
            port (int): The port number for the RDS instance.
            username (str): The database username.

        Returns:
            str: The generated IAM authentication token if successful.
            None: If an error occurs during token generation.
        """
        try:
            session = boto3.session.Session()
            client = session.client(
                service_name="rds", region_name=environ.get("AWS_REGION")
            )
            token = client.generate_db_auth_token(
                DBHostname=host, DBUsername=username, Port=port
            )
            return urllib.parse.quote_plus(token)
        except Exception as e:
            logger.error(f"An error occurred while generating the IAM auth token: {e}")
            return None
