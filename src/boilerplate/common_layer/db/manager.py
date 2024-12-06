
import datetime
import time
from common_layer.db import BodsDB
from common_layer.logger import logger

db_instance = None
token_expiration_time = None


class DbManager:
    """
    Class to manage DB as a global object
    """

    @staticmethod
    def get_db():
        """
        Property to access the database connection object with token expiration handling,
        reusing the global database engine while creating a new session per invocation
        """
        global db_instance
        global token_expiration_time

        current_time = time.time()

        if (
            db_instance is None
            or token_expiration_time is None
            or current_time >= token_expiration_time
        ):
            logger.debug(
                "Initialising new BodsDB instance with refreshed IAM authentication token"
            )
            db_instance, token_expiration_time = DbManager._initialise_db()
        else:
            logger.debug("Re-using cached BodsDB instance as still valid")

        return db_instance

    @staticmethod
    def _initialise_db():
        """
        Initialises the BodsDB instance and sets the token expiration time.
        """
        db = BodsDB()
        token_expiration = (
            time.time() + (15 * 60) - 30
        )  # AWS default token expiration is 15 minutes. Settings to time less 30s as safeguard
        logger.debug(
            f"New token expiration set for {datetime.datetime.utcfromtimestamp(token_expiration)}"
        )
        return db, token_expiration
