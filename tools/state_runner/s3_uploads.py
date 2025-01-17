"""
Module to define the functionality to upload the file for state runner
"""

from typing import Optional

import boto3
import structlog
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    ProfileNotFound,
)
from structlog.stdlib import get_logger

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ]
)

logger = get_logger()


class SessionCreationError(Exception):
    """
    Custom exception for session creation failures.
    """

    pass


class FileUploadError(Exception):
    """Custom exception for S3 file upload failures."""

    pass


def create_aws_session(profile: Optional[str], region: str) -> boto3.Session:
    """
    Creates AWS session with optional profile
    """
    try:
        return (
            boto3.Session(profile_name=profile, region_name=region)
            if profile
            else (boto3.Session(region_name=region))
        )

    except ProfileNotFound as e:
        logger.error(
            "Profile not found. Ensure it is configured in your AWS CLI.",
            profile=profile,
            error=str(e),
        )
        raise SessionCreationError(
            f"Profile '{profile}' not found. Ensure it is configured in your AWS CLI."
        ) from e
    except NoCredentialsError as e:
        logger.error(
            "No AWS credentials found. Please configure them with 'aws configure'.",
            error=str(e),
        )
        raise SessionCreationError(
            "No AWS credentials found. Please configure them with 'aws configure'."
        ) from e
    except Exception as e:
        logger.error(
            "An unexpected error occurred while creating the AWS session.",
            error=str(e),
        )
        raise SessionCreationError(
            f"An unexpected error occurred while creating the AWS session: {e}"
        ) from e


def upload_to_s3(s3_client, file_name, bucket_name, object_name=None):
    """
    Upload a file to an S3 bucket.
    """
    try:
        logger.info(
            "Uploading file to s3",
            from_location=file_name,
            bucket=bucket_name,
            key=object_name,
        )
        # Upload the file
        s3_client.upload_file(file_name, bucket_name, object_name)
        logger.info("File uploaded successfully!", bucket=bucket_name, key=object_name)
        return True
    except ClientError as e:
        logger.error(
            "Failed to upload file to bucket.",
            bucket=bucket_name,
            key=object_name,
            error=str(e),
        )
        raise FileUploadError(
            f"Failed to upload file '{file_name}' to bucket '{bucket_name}/{object_name}': {e}"
        ) from e
    except FileNotFoundError as e:
        logger.error(
            "File not found",
            file_name=file_name,
            error=str(e),
        )
        raise FileUploadError(f"File '{file_name}' not found: {e}") from e
    except BotoCoreError as e:
        logger.error(
            "An error occurred while uploading the file",
            bucket=bucket_name,
            key=object_name,
            error=str(e),
        )
        raise FileUploadError(f"An error occurred while uploading the file: {e}") from e
    except Exception as e:
        logger.error(
            "An error occurred while uploading the file",
            file_name=file_name,
            bucket=bucket_name,
            key=object_name,
            error=str(e),
        )
        raise FileUploadError(f"Unexpected error: {e}") from e
