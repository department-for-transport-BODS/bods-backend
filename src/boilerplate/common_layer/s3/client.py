"""
Description: Module to provide access to S3 objects
"""

import mimetypes
import os
import shutil
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Iterator

import boto3
import botocore.config
from botocore.exceptions import BotoCoreError, ClientError
from botocore.response import StreamingBody
from structlog.stdlib import get_logger

logger = get_logger()


class S3:
    """
    Description: Class to provide access to S3 objects
    """

    def __init__(self, bucket_name: str):
        self._client = self._create_s3_client()
        self._bucket_name = bucket_name

    @property
    def bucket_name(self) -> str:
        """
        S3 Bucket Name configured for Client
        """
        return self._bucket_name

    def _create_s3_client(self):
        #     """
        #     Creates an S3 client. If running locally (PROJECT_ENV=local),
        #     it points to the LocalStack S3 service; otherwise, it connects to AWS
        #     S3.
        #     """
        #     if os.environ.get("PROJECT_ENV") == "local":
        #         logger.info("Using LocalStack for S3 (local environment)")
        #         return boto3.client(
        #             "s3",
        #             endpoint_url="http://host.docker.internal:4566",
        #             aws_access_key_id="dummy",
        #             aws_secret_access_key="dummy",
        #         )
        logger.info("Using AWS S3 (production or non-local environment)")
        config = botocore.config.Config(proxies={})
        return boto3.client("s3", config=config)

    def _get_content_type(self, file_path: str) -> str:
        """
        Try to guess content type via it's path
        Defaults to binary/octet-stream if type cannot be guessed
        """
        content_type, _ = mimetypes.guess_type(file_path)

        if content_type is None:
            content_type = "application/octet-stream"
        logger.debug("S3: Determined Content Type", content_type=content_type)
        return content_type

    def put_object(self, file_path: str, file_data: bytes):
        """
        Upload File data to S3
        """
        logger.info(
            "S3: Uploading file",
            bucket_name=self.bucket_name,
            object_key=file_path,
        )

        content_type = self._get_content_type(file_path)

        try:
            self._client.put_object(
                Bucket=self.bucket_name,
                Key=file_path,
                Body=file_data,
                ContentType=content_type,
            )
            logger.info(
                "S3: Uploaded file successfully",
                bucket_name=self.bucket_name,
                object_key=file_path,
            )
            return True
        except (ClientError, BotoCoreError) as err:
            logger.error(f"Error uploading file {file_path}: {err}")
            raise err

    def download_fileobj(self, file_path: str) -> BytesIO:
        """
        Get S3 Object as BytesIO
        """
        try:
            file_stream = BytesIO()
            self._client.download_fileobj(
                Bucket=self._bucket_name, Key=file_path, Fileobj=file_stream
            )
            file_stream.seek(0)
            return file_stream
        except (ClientError, BotoCoreError) as err:
            logger.error(
                "S3: Error downloading file",
                bucket_name=self.bucket_name,
                object_key=file_path,
                exc_info=True,
            )
            raise err

    def get_object(self, file_path: str) -> StreamingBody:
        """
        Get S3 Object as StreamingBody
        """
        try:
            response = self._client.get_object(Bucket=self._bucket_name, Key=file_path)
            return response["Body"]
        except (ClientError, BotoCoreError) as err:
            logger.error(
                "S3: Error downloading file object",
                bucket_name=self.bucket_name,
                object_key=file_path,
                exc_info=True,
            )
            raise err

    def get_list_objects_v2(self, prefix: str) -> Iterator:
        """
        Return the ListObjectsV2PaginatorOutput as an Iterator
        """

        paginator = self._client.get_paginator("list_objects_v2")
        yield from paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)

    def download_to_tempfile(self, file_path: str) -> Path:
        """
        Downloads S3 object to a temporary file, preserving the original filename.
        Returns the temp file path.
        """

        logger.info(
            "S3: Downloading file to tempfile",
            bucket_name=self.bucket_name,
            object_key=file_path,
        )

        # Get just the filename without the path
        filename = Path(file_path).name
        temp_dir: str | None = None

        try:
            # Create temp dir to store the file with original name
            temp_dir = tempfile.mkdtemp(prefix="s3_download_")
            temp_path = Path(temp_dir) / filename

            # Download directly to the temp file
            with temp_path.open("wb") as temp_file:
                self._client.download_fileobj(
                    Bucket=self._bucket_name, Key=file_path, Fileobj=temp_file
                )

            logger.info(
                "S3: Successfully downloaded to tempfile",
                bucket_name=self.bucket_name,
                object_key=file_path,
                temp_path=str(temp_path),
            )

            return temp_path

        except (ClientError, BotoCoreError):

            logger.error(
                "S3: Error downloading file to tempfile",
                bucket_name=self.bucket_name,
                object_key=file_path,
                exc_info=True,
            )
            if temp_dir is not None:
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise

    def upload_fileobj_streaming(
        self,
        fileobj: BytesIO,
        file_path: str,
        content_type: str | None = None,
    ) -> None:
        """
        Upload a file-like object to S3 using streaming upload.
        This method is more memory-efficient than put_object as it:
        - Streams the data instead of loading it all into memory
        - Automatically handles multipart uploads for large files
        - Is ideal for large files or when memory usage is a concern

        Args:
            fileobj: A file-like object supporting read() and seek()
            file_path: The S3 key (path) where the file should be uploaded
            content_type: Optional content type. If not provided, will be guessed from file_path
        """
        logger.info(
            "S3: Starting streaming upload",
            bucket_name=self.bucket_name,
            object_key=file_path,
        )

        try:
            fileobj.seek(0)
            extra_args = {
                "ContentType": content_type or self._get_content_type(file_path)
            }

            self._client.upload_fileobj(
                Fileobj=fileobj,
                Bucket=self.bucket_name,
                Key=file_path,
                ExtraArgs=extra_args,
            )

            logger.info(
                "S3: Completed streaming upload successfully",
                bucket_name=self.bucket_name,
                object_key=file_path,
            )
        except (ClientError, BotoCoreError) as err:
            logger.error(
                "S3: Error during streaming upload",
                bucket_name=self.bucket_name,
                object_key=file_path,
                exc_info=True,
            )
            raise err
