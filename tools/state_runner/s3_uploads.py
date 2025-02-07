"""
Module to define the functionality to upload the file for state runner
"""

import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    ProfileNotFound,
)
from mypy_boto3_s3 import S3Client

from .state_machines import logger


class SessionCreationError(Exception):
    """
    Custom exception for session creation failures.
    """


class FileUploadError(Exception):
    """Custom exception for S3 file upload failures."""


def create_aws_session(profile: str | None, region: str) -> boto3.Session:
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
        message = (
            f"Profile '{profile}' not found. Ensure it is configured in your AWS CLI."
        )
        logger.error(message, exc_info=True)
        raise SessionCreationError(message) from e
    except NoCredentialsError as e:
        message = (
            "No AWS credentials found. Please configure them with 'aws configure'."
        )
        logger.error(message, exc_info=True)
        raise SessionCreationError(message) from e
    except Exception as e:
        message = "An unexpected error occurred while creating the AWS session."
        logger.error(message, exc_info=True)
        raise SessionCreationError(message) from e


def upload_to_s3(
    s3_client: S3Client, file_name: str, bucket_name: str, object_name: str
):
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
        msg = f"Failed to upload file '{file_name}' to bucket '{bucket_name}/{object_name}'"
        logger.error(msg, exc_info=True)
        raise FileUploadError(msg) from e
    except FileNotFoundError as e:
        msg = f"File '{file_name}' not found"
        logger.error(msg, exc_info=True)
        raise FileUploadError(msg) from e
    except BotoCoreError as e:
        msg = "BotoCoreError occurred while uploading the file"
        logger.error(msg, exc_info=True)
        raise FileUploadError(msg) from e
    except Exception as e:
        msg = "Unexpected error while uploading the file"
        logger.error(msg, exc_info=True)
        raise FileUploadError(msg) from e
