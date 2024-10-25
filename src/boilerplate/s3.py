import boto3
from os import environ
from logger import logger
import io


class S3:
    def __init__(self, filename: str, zipfile, bucket_name: str):
        self._filename = filename
        self._zipfile = zipfile
        self._client = self._create_s3_client()
        self._bucket_name = bucket_name

    def _create_s3_client(self):
        """
        Creates an S3 client. If running locally (PROJECT_ENV=local),
        it points to the LocalStack S3 service; otherwise, it connects to AWS S3.
        """
        if environ.get("PROJECT_ENV") == "local":
            logger.info("Using LocalStack for S3 (local environment)")
            return boto3.client(
                "s3",
                endpoint_url="http://localstack:4566",
                aws_access_key_id="dummy",
                aws_secret_access_key="dummy",
            )
        else:
            logger.info("Using AWS S3 (production or non-local environment)")
            return boto3.client("s3")

    def upload_file(self):
        logger.info("Uploading file to S3")
        self._client.put_object(
            Bucket=self._bucket_name, Key=self._filename, Body=self._zipfile.getvalue()
        )
        logger.info("File uploaded to S3 successfully.")
        return

    def get_fileobj(self, file_path):
        file_stream = io.BytesIO()
        self._client.download_fileobj(Bucket=self._bucket_name, Key=file_path, Fileobj=file_stream)
        file_stream.seek(0)
        return file_stream

