"""
Description: Module to provide access to S3 objects
"""

import asyncio
import functools
import mimetypes
import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

import boto3
import botocore.config
from botocore.exceptions import BotoCoreError, ClientError
from botocore.response import StreamingBody
from structlog.stdlib import get_logger

from .models import ListObjectsV2OutputTypeDef
from .utils import format_s3_tags

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
logger = get_logger()


class S3:
    """
    Description: Class to provide access to S3 objects
    """

    def __init__(self, bucket_name: str, max_workers: int = 150):
        self._client: "S3Client" = self._create_s3_client()
        self._bucket_name: str = bucket_name
        self.max_workers: int = max_workers
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)

    @property
    def bucket_name(self) -> str:
        """
        S3 Bucket Name configured for Client
        """
        return self._bucket_name

    def _create_s3_client(self) -> "S3Client":
        """
        Creates an S3 client. If running locally (PROJECT_ENV=local),
        it points to the LocalStack S3 service; otherwise, it connects to AWS
        S3.
        """
        if os.environ.get("PROJECT_ENV") == "local":
            logger.info("Using LocalStack for S3 (local environment)")
            return boto3.client(  # type: ignore
                "s3",
                endpoint_url="http://host.docker.internal:4566",
                aws_access_key_id="dummy",
                aws_secret_access_key="dummy",
            )
        logger.info("Using AWS S3 (production or non-local environment)")
        config = botocore.config.Config(proxies={}, max_pool_connections=150)
        return boto3.client("s3", config=config)  # type: ignore

    def _get_content_type(self, file_path: str) -> str:
        """
        Try to guess content type via it's path
        Defaults to binary/octet-stream if type cannot be guessed
        """
        content_type, _ = mimetypes.guess_type(file_path)

        if content_type is None:
            content_type = "application/octet-stream"
        return content_type

    def put_object(
        self, file_path: str, file_data: bytes, tags: dict[str, str] | None = None
    ):
        """
        Upload File data to S3
        """
        logger.info(
            "S3: Uploading file",
            bucket_name=self.bucket_name,
            object_key=file_path,
        )

        content_type = self._get_content_type(file_path)
        tagging_str = format_s3_tags(tags)
        try:
            if tagging_str:
                logger.debug(
                    "S3: Adding tags to object", object_key=file_path, tags=tags
                )

                self._client.put_object(
                    Bucket=self.bucket_name,
                    Key=file_path,
                    Body=file_data,
                    ContentType=content_type,
                    Tagging=tagging_str,
                )
            else:
                self._client.put_object(
                    Bucket=self.bucket_name,
                    Key=file_path,
                    Body=file_data,
                    ContentType=content_type,
                )

            return True
        except (ClientError, BotoCoreError) as err:
            logger.error("Error uploading file", file_path=file_path, exc_info=True)
            raise err

    async def put_object_async(
        self, file_path: str, file_data: bytes, tags: dict[str, str] | None = None
    ) -> bool:
        """
        Async version of put_object that uploads file data to S3

        """
        content_type = self._get_content_type(file_path)
        tagging_str = format_s3_tags(tags)

        loop = asyncio.get_running_loop()

        try:
            if tagging_str:
                await loop.run_in_executor(
                    self.thread_pool,
                    functools.partial(
                        self._client.put_object,
                        Bucket=self.bucket_name,
                        Key=file_path,
                        Body=file_data,
                        ContentType=content_type,
                        Tagging=tagging_str,
                    ),
                )
            else:
                await loop.run_in_executor(
                    self.thread_pool,
                    functools.partial(
                        self._client.put_object,
                        Bucket=self.bucket_name,
                        Key=file_path,
                        Body=file_data,
                        ContentType=content_type,
                    ),
                )

            return True
        except (ClientError, BotoCoreError) as err:
            logger.error(
                "Error uploading file async", file_path=file_path, exc_info=True
            )
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

    def get_list_objects_v2(self, prefix: str) -> Iterator[ListObjectsV2OutputTypeDef]:
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

    def get_file_size(self, file_path: str) -> int:
        """
        Gets the size of an S3 object in bytes without downloading it.
        """
        response = self._client.head_object(Bucket=self._bucket_name, Key=file_path)
        return response["ContentLength"]
