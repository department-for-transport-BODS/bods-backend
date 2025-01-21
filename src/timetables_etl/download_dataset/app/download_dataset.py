"""
DownloadDatasetLambda lambda function
"""

from pathlib import Path

from common_layer.database import SqlDB
from common_layer.database.repos import OrganisationDatasetRevisionRepo
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.json_logging import configure_logging
from common_layer.s3 import S3
from pydantic import AnyUrl
from structlog.stdlib import get_logger

from .db_operations import get_remote_file_name, update_dataset_revision
from .file_download import download_revision_linked_file, download_url_to_tempfile
from .models import DownloadDatasetInputData

log = get_logger()


def upload_file_to_s3(temp_filename: Path, filename: str, s3_handler: S3) -> None:
    """
    Upload the file to s3 bucket
    """
    with open(temp_filename, "rb") as temp_file_data:
        s3_handler.put_object(filename, temp_file_data.read())


def download_and_upload_dataset(
    db: SqlDB,
    s3_bucket_name: str,
    revision_id: int,
    url_link: AnyUrl,
) -> dict:
    """
    Template function to download the dataset, upload to S3 and update the database.
    This function downloads the file, uploads it to S3, and updates the revision in the DB.
    """
    revision_repo = OrganisationDatasetRevisionRepo(db)
    revision = revision_repo.get_by_id(revision_id)
    if revision is None:
        raise ValueError("OrganisationDatasetRevision Not Found")
    s3_handler = S3(bucket_name=s3_bucket_name)
    response = download_revision_linked_file(revision)
    file_name = get_remote_file_name(revision, response)
    temp_file_name = download_url_to_tempfile(url_link)
    if temp_file_name is None:
        raise ValueError("File was not downloaded")
    upload_file_to_s3(temp_file_name, file_name, s3_handler)
    update_dataset_revision(db, revision, file_name)
    return {"statusCode": 200, "body": "file downloaded successfully"}


@file_processing_result_to_db(step_name=StepName.DOWNLOAD_DATASET)
def lambda_handler(event, _context) -> dict:
    """
    Lambda Handler for DownloadDatasetLambda
    Downloads a Zip or TransXchange file from a specified URL
    """
    configure_logging()
    log.debug("Input Data", data=event)
    input_data = DownloadDatasetInputData(**event)
    db = SqlDB()
    if input_data.remote_dataset_url_link:
        return download_and_upload_dataset(
            db,
            input_data.s3_bucket_name,
            input_data.revision_id,
            input_data.remote_dataset_url_link,
        )
    log.info("url link is not specified, nothing to download.")
    return {
        "statusCode": 200,
        "body": "url link is not specified, nothing to download",
    }
