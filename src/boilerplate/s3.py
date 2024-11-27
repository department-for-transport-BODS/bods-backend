"""
Description: Module to provide access to S3 objects
"""
from io import BytesIO
import os

import boto3
from botocore.response import StreamingBody
from botocore.exceptions import (
    ClientError,
    BotoCoreError)
from logger import logger


class S3:
    """
    Description: Class to provide access to S3 objects
    """
    def __init__(self, bucket_name: str):
        self._client = self._create_s3_client()
        self._bucket_name = bucket_name

    @property
    def bucket_name(self) -> str:
        return self._bucket_name

    def _create_s3_client(self):# noqa
        """
        Creates an S3 client. If running locally (PROJECT_ENV=local),
        it points to the LocalStack S3 service; otherwise, it connects to AWS
        S3.
        """
        if os.environ.get("PROJECT_ENV") == "local":
            logger.info("Using LocalStack for S3 (local environment)")
            return boto3.client(
                "s3",
                endpoint_url="http://localhost:4566",
                aws_access_key_id="dummy",
                aws_secret_access_key="dummy",
            )
        else:
            logger.info("Using AWS S3 (production or non-local environment)")
            return boto3.client("s3")

    def put_object(self, file_path: str, file_data: bytes):
        logger.info(f"Uploading file to {self.bucket_name}/{file_path}")

        # Determine the content type based on file extension
        content_type = None
        extension = os.path.splitext(file_path)[-1].lower()

        if extension == '.zip':
            content_type = 'application/zip'
        elif extension == '.xml':
            content_type = 'application/xml'
        elif extension == '.csv':
            content_type = 'text/csv'
        elif extension == '.txt':
            content_type = 'text/plain'

        try:
            # Upload the file with appropriate content type
            self._client.put_object(
                Bucket=self.bucket_name,
                Key=file_path,
                Body=file_data,
                ContentType=content_type
            )
            logger.info(f"Uploaded file successfully to "
                        f"{self.bucket_name}/{file_path}")
            return True
        except (ClientError, BotoCoreError) as err:
            logger.error(f"Error uploading file {file_path}: {err}")
            raise err

    def download_fileobj(self, file_path) -> BytesIO: # noqa
        try:
            file_stream = BytesIO()
            self._client.download_fileobj(
                Bucket=self._bucket_name,
                Key=file_path,
                Fileobj=file_stream
            )
            file_stream.seek(0)
            return file_stream
        except (ClientError, BotoCoreError) as err:
            logger.error(f"Error downloading file "
                         f"{self.bucket_name}/{file_path}: {err}")
            raise err

    def get_object(self, file_path: str) -> StreamingBody:
        try:
            response = self._client.get_object(Bucket=self._bucket_name,
                                               Key=file_path)
            return response["Body"]
        except (ClientError, BotoCoreError) as err:
            logger.error(f"Error downloading file object "
                         f"{self.bucket_name}/{file_path}: {err}")
            raise err
